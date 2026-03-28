// Service Worker for Web Push Notifications

self.addEventListener('push', function(event) {
    if (!event.data) return;

    const data = event.data.json();

    const options = {
        body: data.body || 'Check the live dashboard for class statistics!',
        icon: data.icon || '/css/icon-192.png',
        badge: '/css/icon-192.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        },
        actions: [
            { action: 'open', title: 'View Dashboard' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || '📊 Marks Dashboard', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    const targetUrl = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            // If a window with the dashboard is already open, focus it
            for (const client of clientList) {
                if (client.url.includes(targetUrl) && 'focus' in client) {
                    return client.focus();
                }
            }
            // Otherwise open a new window
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
