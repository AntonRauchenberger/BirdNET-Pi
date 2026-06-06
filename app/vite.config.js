import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
    base: "/BirdNET-Pi/",
    plugins: [
        react(),
        VitePWA({
            registerType: "autoUpdate",
            includeAssets: ["favicon.svg", "icon-192.png", "icon-512.png"],
            injectRegister: "auto",
            workbox: {
                globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
                navigateFallback: "/index.html",
                cleanupOutdatedCaches: true,
                clientsClaim: true,
                skipWaiting: true,
                runtimeCaching: [
                    {
                        urlPattern: ({ url }) =>
                            url.origin === "http://192.168.4.1" &&
                            (/^\/sync(\/|$)/.test(url.pathname) ||
                                /^\/device(\/|$)/.test(url.pathname) ||
                                /^\/latestdetections(\/|$)/.test(url.pathname)),
                        handler: "NetworkFirst",
                        options: {
                            cacheName: "api-cache",
                            expiration: {
                                maxEntries: 100,
                                maxAgeSeconds: 60 * 60 * 24,
                            },
                            networkTimeoutSeconds: 3,
                        },
                    },
                ],
            },
            manifest: {
                name: "BirdNET-Pi",
                short_name: "BirdNET-Pi",
                start_url: "/BirdNET-Pi/",
                scope: "/BirdNET-Pi/",
                display: "standalone",
                background_color: "#ffffff",
                theme_color: "#111111",
                icons: [
                    {
                        src: "/icon-192.png",
                        sizes: "192x192",
                        type: "image/png",
                    },
                    {
                        src: "/icon-512.png",
                        sizes: "512x512",
                        type: "image/png",
                    },
                    {
                        src: "/icon-512.png",
                        sizes: "512x512",
                        type: "image/png",
                        purpose: "maskable",
                    },
                ],
            },
        }),
    ],
    server: {
        host: true,
        allowedHosts: ["2896-91-106-123-187.ngrok-free.app"],
    },
});
