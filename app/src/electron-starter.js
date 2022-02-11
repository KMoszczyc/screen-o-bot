// Modules to control application life and create native browser window
const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const isDev = require("electron-is-dev");
const { PythonShell } = require("python-shell");
const log = require("electron-log");
const { sign } = require("crypto");

ipcMain.on("openRecorder", (event, data) => createRecorderWindow());
// ipcMain.on("openPythonRenderer", (event, data) => createPythonWindow());
ipcMain.on("openPythonRenderer", (event, data) => runPython());

const runPython = () => {
  let pyshell = new PythonShell(
    (script = "../backend/src/test.py"),
    (options = {mode: "text"})
  );

  pyshell.send("this is the input")

  pyshell.on("message", function (message) {
    log.info(message);
  });
  pyshell.end(function (err, code, signal) {
    if (err) throw err;
    log.info("done");
  });
};

const createRecorderWindow = () => {
  //TODO: check if window can be made click-through but draggable
  const recorderWindow = new BrowserWindow({
    width: 400,
    height: 300,
    title: "recorder",
    alwaysOnTop: true,
    opacity: 0.2,
    // transparent:true,
    resizable: true,
    // webPreferences: {
    // preload: path.join(__dirname, "preloadRecorder.js"),
    // },
  });
  // recorderWindow.setIgnoreMouseEvents(true);
  recorderWindow.menuBarVisible = false;
  recorderWindow.minimizable = false;

  const getWindowCoordinates = setInterval(() => {
    [xpos, ypos] = recorderWindow.getPosition();
    [width, height] = recorderWindow.getSize();
    log.info({
      height: height,
      width: width,
      ypos: ypos,
      xpos: xpos,
    });
  }, 2000);

  if (recorderWindow.isEnabled) getWindowCoordinates;
  recorderWindow.on("close", function () {
    clearInterval(getWindowCoordinates);
  });
};

const createPythonWindow = () => {
  const pyWindow = new BrowserWindow({
    width: 400,
    height: 300,
    title: "python shell",
  });
};

function createMainWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    title: "Loading...",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nativeWindowOpen: true,
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // load the index.html of the app.
  const startUrl =
    process.env.ELECTRON_START_URL ||
    url.format({
      pathname: path.join(__dirname, "/../build/index.html"),
      protocol: "file:",
      slashes: true,
    });
  if (isDev) mainWindow.loadURL("http://localhost:3000");
  else mainWindow.loadURL(startUrl);

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  createMainWindow();
  // createRecorderWindow();

  app.on("activate", function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", function () {
  if (process.platform !== "darwin") app.quit();
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
