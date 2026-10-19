const { BrowserWindow, ipcMain } = require("electron");
const { resolve } = require("node:path");
function makeWindow() {
 const win = new BrowserWindow({ webPreferences: { preload: resolve(__dirname, "preload.js") } });
 win.loadFile("index.html");
 return win;
}
ipcMain.handle("wb:preview", (_event, value) => value * 2);
module.exports = { makeWindow };
throw new Error("REA_FIXTURE_MUST_NOT_EXECUTE");
