//! VoiceForge desktop: Tauri + D-Bus client for com.voiceforge.App

use tauri::Emitter;

mod commands;
mod dbus_signals;
mod tray;

pub const DBUS_NAME: &str = "com.voiceforge.App";
pub const DBUS_PATH: &str = "/com/voiceforge/App";
pub const DBUS_INTERFACE: &str = "com.voiceforge.App";

pub async fn connection() -> Result<zbus::Connection, String> {
    zbus::Connection::session().await.map_err(|e| e.to_string())
}

pub async fn call_method0(conn: &zbus::Connection, method: &str) -> Result<String, String> {
    let reply = conn
        .call_method(
            Some(DBUS_NAME),
            DBUS_PATH,
            Some(DBUS_INTERFACE),
            method,
            &(),
        )
        .await
        .map_err(|e| e.to_string())?;
    let body: String = reply.body().deserialize().map_err(|e| e.to_string())?;
    Ok(body)
}

#[derive(Clone, serde::Serialize)]
struct SecondInstancePayload {
    args: Vec<String>,
    cwd: String,
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, args, cwd| {
            let _ = app.emit("second-instance", SecondInstancePayload { args, cwd });
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            #[cfg(any(windows, target_os = "linux"))]
            {
                use tauri_plugin_deep_link::DeepLinkExt;
                let _ = app.deep_link().register_all();
            }
            #[cfg(target_os = "macos")]
            {
                use tauri_plugin_deep_link::DeepLinkExt;
                let _ = app.deep_link().register("voiceforge");
            }
            dbus_signals::spawn_signal_listener(app.handle().clone());
            if let Err(e) = tray::setup_tray(app) {
                eprintln!("tray setup failed: {}", e);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::ping,
            commands::get_daemon_version,
            commands::get_settings,
            commands::get_sessions,
            commands::get_session_ids_with_action_items,
            commands::search_transcripts,
            commands::search_rag,
            commands::get_session_detail,
            commands::get_analytics,
            commands::is_listening,
            commands::listen_start,
            commands::listen_stop,
            commands::analyze,
            commands::get_streaming_transcript,
            commands::get_upcoming_calendar_events,
            commands::create_event_from_session,
            commands::set_tray_theme,
            commands::export_session,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
