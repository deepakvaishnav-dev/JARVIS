import { app, BrowserWindow } from "electron";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    titleBarStyle: "hidden",
    titleBarOverlay: {
      color: "#0f172a",
      symbolColor: "#38bdf8",
      height: 30,
    },
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
    backgroundColor: "#0f172a",
    icon: path.join(__dirname, "public/vite.svg"), // Placeholder icon
  });

  // Check if we are in development mode (Vite dev server)
  const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    // Open the DevTools.
    // mainWindow.webContents.openDevTools();
  } else {
    // In production, load the built index.html
    mainWindow.loadFile(path.join(__dirname, "dist", "index.html"));
  }

  mainWindow.on("closed", function () {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", function () {
  if (process.platform !== "darwin") app.quit();
});
