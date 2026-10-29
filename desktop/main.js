const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const { url } = require("./config.json");

let ventana;

function abrirFuera(destino) {
  if (/^https?:\/\//i.test(destino)) shell.openExternal(destino);
}

function crear() {
  const origen = new URL(url).origin;
  ventana = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 380,
    minHeight: 600,
    title: "Gestión de Condominio",
    icon: path.join(__dirname, "build", "icon.png"),
    backgroundColor: "#121A19",
    autoHideMenuBar: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });

  // Los enlaces a otros sitios (por ejemplo WhatsApp) se abren en el navegador
  ventana.webContents.setWindowOpenHandler(({ url: destino }) => {
    abrirFuera(destino);
    return { action: "deny" };
  });
  ventana.webContents.on("will-navigate", (e, destino) => {
    if (destino.startsWith("file:")) return;
    if (new URL(destino).origin !== origen) {
      e.preventDefault();
      abrirFuera(destino);
    }
  });

  // Sin internet o servidor caído: pantalla con botón para reintentar
  ventana.webContents.on("did-fail-load", (_e, codigo, _desc, _url, principal) => {
    if (principal && codigo !== -3) {
      ventana.loadFile(path.join(__dirname, "sin-conexion.html"), { query: { u: url } });
    }
  });

  // Pantalla de carga mientras el servidor gratuito despierta (puede tardar ~1 minuto)
  ventana
    .loadFile(path.join(__dirname, "cargando.html"))
    .then(() => ventana.loadURL(url))
    .catch(() => {});
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.whenReady().then(crear);
  app.on("second-instance", () => {
    if (ventana) {
      if (ventana.isMinimized()) ventana.restore();
      ventana.focus();
    }
  });
  app.on("window-all-closed", () => app.quit());
}
