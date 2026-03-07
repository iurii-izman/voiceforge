//! System tray: menu (Open, Toggle recording, Quit), click to show/hide window.
//! Tray icon can be switched by theme (light/dark) via set_tray_theme command (#87).

use tauri::{
    image::Image,
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Emitter, Manager, Runtime,
};

const TRAY_ID: &str = "main";
const ID_OPEN: &str = "tray-open";
const ID_TOGGLE: &str = "tray-toggle-record";
const ID_QUIT: &str = "tray-quit";

/// Light theme tray icon (default). Dark icon: add icons/icon-dark.png and use in set_tray_theme.
fn tray_icon_light() -> Result<Image<'static>, Box<dyn std::error::Error + Send + Sync>> {
    let bytes = include_bytes!("../icons/icon.png");
    Image::from_bytes(bytes).map_err(|e| e.into())
}

pub fn setup_tray<R: Runtime>(app: &tauri::App<R>) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let open_i = MenuItem::with_id(app, ID_OPEN, "Открыть", true, None::<&str>)?;
    let toggle_i = MenuItem::with_id(app, ID_TOGGLE, "Старт/стоп записи", true, None::<&str>)?;
    let quit_i = MenuItem::with_id(app, ID_QUIT, "Выход", true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&open_i, &toggle_i, &quit_i])?;

    let icon = tray_icon_light()?;
    let _tray = TrayIconBuilder::with_id(TRAY_ID)
        .icon(icon)
        .menu(&menu)
        .on_menu_event(move |app_handle, event| {
            let id = event.id.as_ref();
            if id == ID_OPEN {
                if let Some(w) = app_handle.get_webview_window("main") {
                    let _ = w.show();
                    let _ = w.set_focus();
                }
            } else if id == ID_TOGGLE {
                let _ = app_handle.emit("tray-toggle-listen", ());
            } else if id == ID_QUIT {
                app_handle.exit(0);
            }
        })
        .on_tray_icon_event(|tray, event| {
            use tauri::tray::TrayIconEvent;
            if let TrayIconEvent::Click { .. } = event {
                if let Some(app) = tray.app_handle().get_webview_window("main") {
                    if app.is_visible().unwrap_or(false) {
                        let _ = app.hide();
                    } else {
                        let _ = app.show();
                        let _ = app.set_focus();
                    }
                }
            }
        })
        .build(app)?;

    Ok(())
}

/// Set tray icon by theme (light/dark). Call from frontend when theme changes (#87).
/// If icons/icon-dark.png exists, it is used for dark theme; otherwise same as light.
pub fn set_tray_theme<R: Runtime>(
    app: &tauri::AppHandle<R>,
    is_dark: bool,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let Some(tray) = app.tray_by_id(TRAY_ID) else {
        return Ok(());
    };
    let icon = if is_dark {
        if let Ok(res_dir) = app.path().resource_dir() {
            let dark_path = res_dir.join("icons").join("icon-dark.png");
            if dark_path.exists() {
                if let Ok(img) = Image::from_path(&dark_path) {
                    img.to_owned()
                } else {
                    tray_icon_light()?
                }
            } else {
                tray_icon_light()?
            }
        } else {
            tray_icon_light()?
        }
    } else {
        tray_icon_light()?
    };
    let _ = tray.set_icon(Some(icon));
    Ok(())
}
