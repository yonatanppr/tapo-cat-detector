# Which push service reaches the iPhone fastest?

Research for #5, checked on 2026-10-19 against each service's own docs, the apps' source code and Apple's docs. Source tags in brackets point to the list at the end.

## Answer

Pushover. Its released iOS app is the only one of the three that can send Critical Alerts today, which sound through the mute switch and Do Not Disturb [P3, A2]. It shows an image in the notification, costs $4.99 once after a 30-day trial, and needs one HTTPS POST from a Worker [P1, P2].

ntfy is the free option. It becomes a close second once its iOS app v1.8.0 ships, since that version adds Critical Alerts [N4]. Telegram is free and easy to call, but its messages cannot get past a Focus or silent mode on their own [T3].

None of the three publishes a delivery time we can compare. All three end at Apple's push service (APNs), so the differences are the hops before APNs and what the app does when the push lands. Measure on the real phone before relying on any of them (see "Open").

## Comparison

| | Pushover | ntfy (ntfy.sh) | Telegram bot |
|---|---|---|---|
| Path to phone | Pushover API, APNs | ntfy.sh, Firebase, APNs [N2] | Bot API, Telegram, APNs |
| Published speed | about 1 s, "often within a few hundred milliseconds" [P4] | none | none |
| Through Focus | yes with Critical Alerts | priority 4 is time-sensitive [N3] | only if Telegram is an allowed app in that Focus [A3] |
| Through silent mode | yes with Critical Alerts | not in the released app; planned for v1.8.0 [N4] | no |
| Image in notification | yes, up to 5 MB [P1] | yes since iOS v1.7.0; free tier uploads up to 2 MB [N4, N6] | sendPhoto up to 10 MB [T1]; banner preview not checked |
| Cost | $4.99 once per platform [P2] | free; paid tiers from 600 cents/month [N6] | free [T2] |
| Limits | 10,000 messages/month [P1] | 250 messages/day; 60-request burst then 1 per 5 s, keyed by IP [N1, N7] | 1 message/s per chat [T2] |
| Secret to keep | app token and user key | topic name, or access token | bot token |

## Pushover

Send with `POST https://api.pushover.net/1/messages.json` and the fields `token`, `user` and `message`. Optional fields include `title`, `priority`, `sound`, and an image as `attachment` (multipart) or `attachment_base64` plus `attachment_type` [P1]. From a Worker that is one `fetch` with a `FormData` or JSON body.

Priorities [P1]:

- Priority 1 (high) skips the user's Pushover quiet hours and always plays a sound.
- Priority 2 (emergency) repeats every `retry` seconds (at least 30) until the user acknowledges it or `expire` runs out (at most 3 hours). It returns a receipt and can call a callback URL.
- Priority does not change queueing or routing, it "only affects how device clients display them".

Critical Alerts: the iOS app got Apple's entitlement in 2020 [P3]. They are off by default; the user turns them on in the app's settings and accepts an iOS prompt. They play at a volume set in Pushover, not the phone's volume [P3]. Since app version 4.2 there are two switches, one for high and one for emergency priority [P5].

Time-sensitive: a user on Pushover's support forum says the iOS app supports it [P6], but I found no first-party page that says which priority uses it. With Critical Alerts on, this does not matter for the counter alert.

Images: one per message, at most 5,242,880 bytes, resized by the sender. The phone downloads the image and shows it with the notification; if the download fails or takes too long, the notification shows without it. The image must be in the request, not a URL, and Pushover deletes it once the device has it [P1].

Limits: 10,000 messages a month on a free account, shared by all its apps. Over that the API returns 429 until the 1st of the next month. Responses carry `X-Limit-App-Remaining`. Use at most 2 concurrent connections, wait at least 5 s before retrying a 5xx, and avoid repeated 4xx errors, which can get the IP blocked for a while [P1].

Speed: Pushover's support says notifications usually arrive in about a second. If they take over 10 s it points at Apple Intelligence notification summaries on newer iPhones and suggests turning them off [P4].

Fit with the map: one priority 1 message per incident with "Critical Alerts for high priority" on gives one loud alert. Emergency priority keeps ringing until acknowledged, which is a burst by design, so only use it if that is wanted. Its receipt could later help the failure watch.

## ntfy

Send with `POST` or `PUT` to `https://ntfy.sh/<topic>`. Headers set `Title`, `Priority` (1 to 5) and `Attach` (a URL). A file sent as the body becomes the attachment [N1].

iOS delivery: for ntfy.sh topics the server pushes through Firebase to APNs. A self-hosted server cannot push to iOS by itself; it has to relay through an upstream such as ntfy.sh, and without that, delivery can take hours [N2].

Priorities on iOS: the released app, v1.7.0, maps priority 4 to time-sensitive and priority 5 to the critical level in code [N3]. That build has no Critical Alerts entitlement [N3], and Apple only lets apps with the entitlement play critical alerts [A2]. Apple does not document what happens to such a notification, so priority 4 is the safe choice for now. v1.8.0, listed as unreleased, makes priority 5 "critical alerts that bypass silent mode and Do Not Disturb" once the user opts in [N4]. On 2026-10-18 the release table still listed iOS v1.7.0 as current [N4].

Images: the iOS app shows images inline since v1.7.0, released 2026-05-30 [N4]. The free tier allows 2 MB per uploaded file and 20 MB in total, and uploads expire after 3 hours [N6]. Attaching by URL avoids those limits [N1], but then the image must sit at a reachable URL.

Limits: each visitor gets a burst of 60 requests, refilled at one every 5 s, and ntfy.sh allows 250 messages a day [N1]. A visitor is its IP address unless the user is on a paid tier [N7]. A Worker sends from Cloudflare's IP addresses, which other Cloudflare customers also use, so an anonymous Worker may share its bucket with strangers. That last part is my inference; I did not measure it.

Security: on the free tier the topic name is the only protection; ntfy's docs call the topic "essentially a password" [N1]. In a public repo it must be kept secret like an API key. Reserved topics need a paid tier [N6].

Cost: the free tier as above. The tiers API lists Supporter at 600 cents a month or 6000 a year, with 2,500 messages a day, 25 MB attachments and 3 reserved topics [N6]. The API does not name the currency.

## Telegram bot

Send with `GET` or `POST` to `https://api.telegram.org/bot<token>/sendMessage` or `/sendPhoto` with `chat_id`, as JSON or multipart [T1]. The token sits in the URL path, so keep request URLs out of logs.

Images: `sendPhoto` takes an upload, a URL or a `file_id`, at most 10 MB [T1]. I did not check whether the iOS banner shows the photo.

Loudness: `disable_notification` sends a message with no sound. There is no flag the other way [T1].

Focus and silent mode: the official iOS build declares the communication-notifications and notification-filtering entitlements, but neither time-sensitive nor critical alerts [T3]. A bot message is therefore an ordinary notification. It gets through a Focus only if Telegram is on that Focus's allowed apps list, and then every Telegram chat gets through too [A3]. It never sounds in silent mode.

Limits: no more than about one message per second per chat, 20 a minute in a group, about 30 a second overall; over that the API returns 429 with `retry_after` [T1, T2].

Cost: free [T2].

## Apple background

Interruption levels [A1]:

- Active is the default. Focus and Notification Summary can hold it back.
- Time-sensitive "breaks through system notification controls", meaning Focus and Notification Summary. The user can turn this off.
- Critical "bypasses the mute switch to play a sound".

Critical alerts need an entitlement that Apple grants on request. With it, an app can play a sound when the phone is locked, muted or in Do Not Disturb [A2].

Each Focus has an allowed apps list and a Time Sensitive Notifications switch that lets every app's time-sensitive notifications through [A3].

For the counter alert this means only a critical alert is sure to sound with the phone muted. Time-sensitive needs that Focus switch on and stays quiet in silent mode.

## Open

- No delivery times were measured. Once an account exists, send about 20 test alerts from the Worker with the send time in the text and note the arrival time with the phone locked, in a Focus and muted.
- Which Pushover priority is time-sensitive. This only matters if Critical Alerts stay off.
- When ntfy iOS v1.8.0 ships. With it, ntfy matches Pushover on Critical Alerts for free, but the shared-IP limit and the public topic remain.

## Sources

- [P1] Pushover Message API: https://pushover.net/api
- [P2] Pushover pricing: https://pushover.net/pricing
- [P3] Pushover blog, iOS Critical Alerts (2020): https://blog.pushover.net/posts/2020/2/ios-critical-alerts
- [P4] Pushover support, delayed notifications: https://support.pushover.net/i281-notifications-are-received-but-after-significant-delay
- [P5] Pushover iOS app, version history (4.2): https://apps.apple.com/us/app/pushover-notifications/id506088175
- [P6] Pushover support forum, time-sensitive request: https://support.pushover.net/i199-medium-priority-0-5-for-time-sensitive-on-ios
- [N1] ntfy publishing docs, including limitations: https://docs.ntfy.sh/publish/
- [N2] ntfy config docs, iOS instant notifications: https://docs.ntfy.sh/config/
- [N3] ntfy iOS v1.7.0 priority mapping and entitlements: https://github.com/binwiederhier/ntfy-ios/blob/v1.7.0/ntfy/Utils/NotificationContent.swift and https://github.com/binwiederhier/ntfy-ios/blob/v1.7.0/ntfy/ntfy.entitlements
- [N4] ntfy release notes: https://github.com/binwiederhier/ntfy/blob/main/docs/releases.md
- [N6] ntfy.sh tiers API: https://ntfy.sh/v1/tiers
- [N7] ntfy server, `visitorID`: https://github.com/binwiederhier/ntfy/blob/main/server/visitor.go
- [T1] Telegram Bot API: https://core.telegram.org/bots/api
- [T2] Telegram Bots FAQ, broadcasting limits: https://core.telegram.org/bots/faq
- [T3] Telegram iOS build file with entitlements: https://github.com/TelegramMessenger/Telegram-iOS/blob/master/Telegram/BUILD
- [A1] Apple, UNNotificationInterruptionLevel: https://developer.apple.com/documentation/usernotifications/unnotificationinterruptionlevel
- [A2] Apple, Critical Alerts entitlement: https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.usernotifications.critical-alerts
- [A3] Apple, allow or silence notifications for a Focus: https://support.apple.com/guide/iphone/allow-or-silence-notifications-for-a-focus-iph21d43af5b/ios
