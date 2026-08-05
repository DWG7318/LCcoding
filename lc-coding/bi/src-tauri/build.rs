fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&[
                "bind_project",
                "choose_project",
                "get_snapshot",
                "is_pinned",
                "set_pinned",
            ])),
    )
    .expect("failed to build the fixed LCCoding desktop manifest");
}
