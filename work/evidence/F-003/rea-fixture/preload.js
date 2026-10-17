const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("study", { preview: value => ipcRenderer.invoke("wb:preview", value) });
