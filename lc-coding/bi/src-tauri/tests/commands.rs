use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;

use lccoding::commands::SingleFlight;

#[test]
fn concurrent_refreshes_join_one_rust_operation_and_a_later_call_restarts() {
    let flight = SingleFlight::<u32, &'static str>::default();
    let calls = Arc::new(AtomicUsize::new(0));

    let (first, second) = tauri::async_runtime::block_on(async {
        let first_calls = Arc::clone(&calls);
        let first = flight.run(move || async move {
            first_calls.fetch_add(1, Ordering::SeqCst);
            tauri::async_runtime::spawn_blocking(|| {
                std::thread::sleep(Duration::from_millis(20));
            })
            .await
            .unwrap();
            Ok(7)
        });
        let second_calls = Arc::clone(&calls);
        let second = flight.run(move || async move {
            second_calls.fetch_add(1, Ordering::SeqCst);
            Ok(99)
        });
        futures_util::join!(first, second)
    });

    assert_eq!(first, second);
    assert!(matches!(first, Ok(7 | 99)));
    assert_eq!(calls.load(Ordering::SeqCst), 1);

    let next_calls = Arc::clone(&calls);
    let next = tauri::async_runtime::block_on(flight.run(move || async move {
        next_calls.fetch_add(1, Ordering::SeqCst);
        Ok(8)
    }));
    assert_eq!(next, Ok(8));
    assert_eq!(calls.load(Ordering::SeqCst), 2);
}

#[test]
fn a_failed_operation_is_shared_then_cleared_without_leaking_its_body() {
    let flight = SingleFlight::<u32, &'static str>::default();
    let calls = Arc::new(AtomicUsize::new(0));
    let (first, second) = tauri::async_runtime::block_on(async {
        let first_calls = Arc::clone(&calls);
        let first = flight.run(move || async move {
            first_calls.fetch_add(1, Ordering::SeqCst);
            tauri::async_runtime::spawn_blocking(|| {
                std::thread::sleep(Duration::from_millis(20));
            })
            .await
            .unwrap();
            Err("fixed-code")
        });
        let second_calls = Arc::clone(&calls);
        let second = flight.run(move || async move {
            second_calls.fetch_add(1, Ordering::SeqCst);
            Err("other-fixed-code")
        });
        futures_util::join!(first, second)
    });
    assert_eq!(first, second);
    assert!(matches!(first, Err("fixed-code" | "other-fixed-code")));
    assert_eq!(calls.load(Ordering::SeqCst), 1);

    let recovered = tauri::async_runtime::block_on(flight.run(|| async { Ok(3) }));
    assert_eq!(recovered, Ok(3));
}
