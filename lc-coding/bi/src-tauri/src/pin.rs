pub const PIN_UNAVAILABLE: &str = "BI_PIN_UNAVAILABLE";

pub trait TopmostWindow {
    type Error;

    fn read_topmost(&self) -> Result<bool, Self::Error>;
    fn set_topmost(&self, enabled: bool) -> Result<(), Self::Error>;
}

pub fn read_confirmed<W: TopmostWindow>(window: &W) -> Result<bool, &'static str> {
    window.read_topmost().map_err(|_| PIN_UNAVAILABLE)
}

pub fn set_and_confirm<W: TopmostWindow>(window: &W, enabled: bool) -> Result<bool, &'static str> {
    window.set_topmost(enabled).map_err(|_| PIN_UNAVAILABLE)?;
    read_confirmed(window)
}

impl<R: tauri::Runtime> TopmostWindow for tauri::WebviewWindow<R> {
    type Error = tauri::Error;

    fn read_topmost(&self) -> Result<bool, Self::Error> {
        self.is_always_on_top()
    }

    fn set_topmost(&self, enabled: bool) -> Result<(), Self::Error> {
        self.set_always_on_top(enabled)
    }
}

#[tauri::command]
pub async fn is_pinned(window: tauri::WebviewWindow) -> Result<bool, &'static str> {
    read_confirmed(&window)
}

#[tauri::command]
pub async fn set_pinned(window: tauri::WebviewWindow, enabled: bool) -> Result<bool, &'static str> {
    set_and_confirm(&window, enabled)
}

#[cfg(test)]
mod tests {
    use std::cell::RefCell;

    use super::{TopmostWindow, read_confirmed, set_and_confirm};

    struct FakeWindow {
        read_result: Result<bool, ()>,
        set_result: Result<(), ()>,
        set_calls: RefCell<Vec<bool>>,
    }

    impl FakeWindow {
        fn new(read_result: Result<bool, ()>, set_result: Result<(), ()>) -> Self {
            Self {
                read_result,
                set_result,
                set_calls: RefCell::new(Vec::new()),
            }
        }
    }

    impl TopmostWindow for FakeWindow {
        type Error = ();

        fn read_topmost(&self) -> Result<bool, Self::Error> {
            self.read_result
        }

        fn set_topmost(&self, enabled: bool) -> Result<(), Self::Error> {
            self.set_calls.borrow_mut().push(enabled);
            self.set_result
        }
    }

    #[test]
    fn read_returns_the_actual_host_state() {
        let window = FakeWindow::new(Ok(true), Ok(()));

        assert_eq!(read_confirmed(&window), Ok(true));
        assert!(window.set_calls.borrow().is_empty());
    }

    #[test]
    fn set_returns_confirmed_host_state_not_the_requested_value() {
        let window = FakeWindow::new(Ok(false), Ok(()));

        assert_eq!(set_and_confirm(&window, true), Ok(false));
        assert_eq!(*window.set_calls.borrow(), vec![true]);
    }

    #[test]
    fn host_failures_map_to_the_path_free_pin_code() {
        let read_failure = FakeWindow::new(Err(()), Ok(()));
        let set_failure = FakeWindow::new(Ok(true), Err(()));

        assert_eq!(read_confirmed(&read_failure), Err("BI_PIN_UNAVAILABLE"));
        assert_eq!(
            set_and_confirm(&set_failure, false),
            Err("BI_PIN_UNAVAILABLE")
        );
        assert_eq!(*set_failure.set_calls.borrow(), vec![false]);
    }
}
