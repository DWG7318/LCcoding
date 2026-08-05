pub mod binding;
mod commands;
mod errors;
pub mod git_reader;
pub mod input;
mod native_picker;
mod pin;

use tauri::webview::{NewWindowResponse, WebviewWindowBuilder};

fn is_packaged_app_url(url: &tauri::Url) -> bool {
    let has_exact_authority =
        url.username().is_empty() && url.password().is_none() && url.port().is_none();

    #[cfg(any(windows, target_os = "android"))]
    {
        has_exact_authority && url.scheme() == "http" && url.host_str() == Some("tauri.localhost")
    }

    #[cfg(not(any(windows, target_os = "android")))]
    {
        has_exact_authority && url.scheme() == "tauri" && url.host_str() == Some("localhost")
    }
}

pub fn run() {
    let binding = binding::BindingState::default();
    match binding::parse_launch_args(std::env::args_os()) {
        Ok(binding::LaunchRequest::Unbound) => {}
        Ok(binding::LaunchRequest::Project(root)) => {
            let _ = binding.bind_root(&root);
        }
        Err(error) => {
            eprintln!("{}", error.code());
            std::process::exit(2);
        }
    }

    if tauri::webview_version().is_err() {
        eprintln!("BI_WEBVIEW_UNAVAILABLE");
        std::process::exit(2);
    }

    let application = tauri::Builder::default()
        .manage(binding)
        .setup(|app| {
            let window_config = app
                .config()
                .app
                .windows
                .iter()
                .find(|window| window.label == "main")
                .ok_or_else(|| std::io::Error::other("BI_DESKTOP_CONFIG_INVALID"))?;

            WebviewWindowBuilder::from_config(app, window_config)?
                .browser_extensions_enabled(false)
                .on_navigation(is_packaged_app_url)
                .on_download(|_, _| false)
                .on_new_window(|_, _| NewWindowResponse::Deny)
                .build()?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::bind_project,
            commands::choose_project,
            commands::get_snapshot,
            pin::is_pinned,
            pin::set_pinned,
        ])
        .run(tauri::generate_context!());

    if application.is_err() {
        eprintln!("BI_DESKTOP_START_FAILED");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::is_packaged_app_url;

    #[cfg(windows)]
    #[test]
    fn windows_allows_only_the_exact_packaged_app_origin() {
        assert!(is_packaged_app_url(
            &"http://tauri.localhost/index.html".parse().unwrap()
        ));

        for rejected in [
            "tauri://localhost/index.html",
            "https://tauri.localhost/index.html",
            "http://tauri.localhost:8080/index.html",
            "http://tauri.localhost.evil.invalid/index.html",
            "http://evil.invalid/index.html",
        ] {
            assert!(
                !is_packaged_app_url(&rejected.parse().unwrap()),
                "{rejected}"
            );
        }
    }
}
