//! Subscribe to D-Bus signals from com.voiceforge.App and emit Tauri events.

use futures_util::StreamExt;
use tauri::{AppHandle, Emitter};
use zbus::message::Type;
use zbus::{MatchRule, MessageStream};

use crate::{connection, DBUS_INTERFACE, DBUS_NAME, DBUS_PATH};

const EVENT_LISTEN_STATE: &str = "listen-state-changed";
const EVENT_ANALYSIS_DONE: &str = "analysis-done";

fn rule_listen_state() -> Result<MatchRule<'static>, zbus::Error> {
    Ok(MatchRule::builder()
        .msg_type(Type::Signal)
        .sender(DBUS_NAME)?
        .path(DBUS_PATH)?
        .interface(DBUS_INTERFACE)?
        .member("ListenStateChanged")?
        .build())
}

fn rule_analysis_done() -> Result<MatchRule<'static>, zbus::Error> {
    Ok(MatchRule::builder()
        .msg_type(Type::Signal)
        .sender(DBUS_NAME)?
        .path(DBUS_PATH)?
        .interface(DBUS_INTERFACE)?
        .member("AnalysisDone")?
        .build())
}

pub fn spawn_signal_listener(app: AppHandle) {
    tauri::async_runtime::spawn(async move {
        let conn = match connection().await {
            Ok(c) => c,
            Err(e) => {
                eprintln!("dbus_signals: connection failed: {}", e);
                return;
            }
        };

        let stream_listen = match MessageStream::for_match_rule(
            rule_listen_state().expect("ListenStateChanged rule"),
            &conn,
            Some(8),
        )
        .await
        {
            Ok(s) => s,
            Err(e) => {
                eprintln!("dbus_signals: ListenStateChanged stream: {}", e);
                return;
            }
        };

        let stream_analysis = match MessageStream::for_match_rule(
            rule_analysis_done().expect("AnalysisDone rule"),
            &conn,
            Some(8),
        )
        .await
        {
            Ok(s) => s,
            Err(e) => {
                eprintln!("dbus_signals: AnalysisDone stream: {}", e);
                return;
            }
        };

        let app_listen = app.clone();
        let app_analysis = app.clone();

        tauri::async_runtime::spawn(async move {
            let mut stream = stream_listen;
            while let Some(res) = stream.next().await {
                if let Ok(msg) = res {
                    if let Ok((is_listening,)) = msg.body().deserialize::<(bool,)>() {
                        let _ = app_listen.emit(EVENT_LISTEN_STATE, serde_json::json!({ "is_listening": is_listening }));
                    }
                }
            }
        });

        tauri::async_runtime::spawn(async move {
            let mut stream = stream_analysis;
            while let Some(res) = stream.next().await {
                if let Ok(msg) = res {
                    if let Ok((status,)) = msg.body().deserialize::<(String,)>() {
                        let _ = app_analysis.emit(EVENT_ANALYSIS_DONE, serde_json::json!({ "status": status }));
                    }
                }
            }
        });
    });
}
