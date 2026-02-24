//! VoiceForge desktop: Tauri + D-Bus client for com.voiceforge.App

mod commands;
mod dbus_signals;

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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            dbus_signals::spawn_signal_listener(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::ping,
            commands::get_settings,
            commands::get_sessions,
            commands::get_session_detail,
            commands::get_analytics,
            commands::is_listening,
            commands::listen_start,
            commands::listen_stop,
            commands::analyze,
            commands::get_streaming_transcript,
            commands::export_session,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
