/** Tauri API shim: delegates to __VOICEFORGE_TEST_HOOKS__ when present (e2e), else real Tauri. */
import { invoke as tauriInvoke } from "@tauri-apps/api/core";
import { listen as tauriListen } from "@tauri-apps/api/event";
import { getCurrentWindow as tauriGetCurrentWindow } from "@tauri-apps/api/window";
import {
  isPermissionGranted as notificationIsPermissionGranted,
  requestPermission as notificationRequestPermission,
  sendNotification as notificationSend,
} from "@tauri-apps/plugin-notification";
import {
  register as shortcutRegister,
  unregister as shortcutUnregister,
} from "@tauri-apps/plugin-global-shortcut";
import { getCurrent as deepLinkGetCurrent, onOpenUrl as deepLinkOnOpenUrl } from "@tauri-apps/plugin-deep-link";
import {
  enable as autostartEnableReal,
  disable as autostartDisableReal,
  isEnabled as autostartIsEnabledReal,
} from "@tauri-apps/plugin-autostart";
import { Store as TauriStore } from "@tauri-apps/plugin-store";
import { check as updaterCheckReal } from "@tauri-apps/plugin-updater";
import { relaunch as relaunchReal } from "@tauri-apps/plugin-process";

function getTestHooks() {
  return globalThis.__VOICEFORGE_TEST_HOOKS__ || null;
}

export function invoke(cmd, args) {
  const hooks = getTestHooks();
  return hooks?.invoke ? hooks.invoke(cmd, args) : tauriInvoke(cmd, args);
}

export function listen(eventName, callback) {
  const hooks = getTestHooks();
  return hooks?.listen ? hooks.listen(eventName, callback) : tauriListen(eventName, callback);
}

export function getCurrentWindow() {
  const hooks = getTestHooks();
  return hooks?.getCurrentWindow ? hooks.getCurrentWindow() : tauriGetCurrentWindow();
}

export { LogicalPosition, LogicalSize } from "@tauri-apps/api/window";

export function isPermissionGranted() {
  const hooks = getTestHooks();
  return hooks?.notification?.isPermissionGranted
    ? hooks.notification.isPermissionGranted()
    : notificationIsPermissionGranted();
}

export function requestPermission() {
  const hooks = getTestHooks();
  return hooks?.notification?.requestPermission
    ? hooks.notification.requestPermission()
    : notificationRequestPermission();
}

export function sendNotification(payload) {
  const hooks = getTestHooks();
  return hooks?.notification?.sendNotification
    ? hooks.notification.sendNotification(payload)
    : notificationSend(payload);
}

export function registerShortcut(shortcuts, handler) {
  const hooks = getTestHooks();
  return hooks?.globalShortcut?.register
    ? hooks.globalShortcut.register(shortcuts, handler)
    : shortcutRegister(shortcuts, handler);
}

export function unregisterShortcut(shortcuts) {
  const hooks = getTestHooks();
  return hooks?.globalShortcut?.unregister
    ? hooks.globalShortcut.unregister(shortcuts)
    : shortcutUnregister(shortcuts);
}

export function getCurrent() {
  const hooks = getTestHooks();
  return hooks?.deepLink?.getCurrent ? hooks.deepLink.getCurrent() : deepLinkGetCurrent();
}

export function onOpenUrl(handler) {
  const hooks = getTestHooks();
  return hooks?.deepLink?.onOpenUrl ? hooks.deepLink.onOpenUrl(handler) : deepLinkOnOpenUrl(handler);
}

export function autostartEnable() {
  const hooks = getTestHooks();
  return hooks?.autostart?.enable ? hooks.autostart.enable() : autostartEnableReal();
}

export function autostartDisable() {
  const hooks = getTestHooks();
  return hooks?.autostart?.disable ? hooks.autostart.disable() : autostartDisableReal();
}

export function autostartIsEnabled() {
  const hooks = getTestHooks();
  return hooks?.autostart?.isEnabled ? hooks.autostart.isEnabled() : autostartIsEnabledReal();
}

export const AppStore = {
  load(name) {
    const hooks = getTestHooks();
    return hooks?.Store?.load ? hooks.Store.load(name) : TauriStore.load(name);
  },
};

export function updaterCheck() {
  const hooks = getTestHooks();
  return hooks?.updater?.check ? hooks.updater.check() : updaterCheckReal();
}

export function relaunch() {
  const hooks = getTestHooks();
  return hooks?.process?.relaunch ? hooks.process.relaunch() : relaunchReal();
}
