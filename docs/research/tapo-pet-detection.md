# Can the Tapo app's own detection do the job alone?

Research for #3. Checked 2026-10-19 against TP-Link's own pages unless noted.

## Answer

No. No hardware version of the Tapo C200 has pet detection, and Tapo Care does
not add it. The camera can only detect motion, people and a crying baby. The
closest the app gets is a motion alert for a zone drawn over the counter. That
alert fires for anything that moves there: people, hands, pots, light changes.
There is also no cooldown, so one busy minute gives a stream of alerts. That is
the same failure mode as the old Frigate setup, minus any classifier.

Recommendation: do not rely on the Tapo app alone. Keep building the cloud
detector from #1. The decision is yours.

## Pet detection by hardware version

TP-Link staff tell users to check a model's spec page to see whether it has
Pet Detection ([community](https://community.tp-link.com/en/home/uc/post/910348?page=737)).
For the C200:

| Hardware | AI detection on the spec page | Source |
|---|---|---|
| V1 | Motion only ("Input Trigger: Motion detection") | [V1 page](https://www.tp-link.com/en/home-networking/cloud-camera/tapo-c200/v1/) |
| V2 | Motion only | [V2 page](https://www.tp-link.com/en/home-networking/cloud-camera/tapo-c200/v2/) |
| V3 | Motion, Person, BabyCry | [V3 page](https://www.tp-link.com/de/home-networking/cloud-camera/tapo-c200/v3/) |
| V3.20 | Motion, Person, BabyCry | [DE page](https://www.tp-link.com/de/home-networking/cloud-camera/tapo-c200/) |
| V4 | No product page; firmware notes mention only motion and person | [V4 downloads](https://www.tp-link.com/de/support/download/tapo-c200/v4/) |
| V5 | Motion, Person, BabyCry | [EN page](https://www.tp-link.com/en/home-networking/cloud-camera/tapo-c200/) |

None of the EU firmware notes for V1, V3, V4 or V5 mention pet detection
([V1](https://www.tp-link.com/de/support/download/tapo-c200/v1/),
[V3](https://www.tp-link.com/de/support/download/tapo-c200/v3/),
[V4](https://www.tp-link.com/de/support/download/tapo-c200/v4/),
[V5](https://www.tp-link.com/de/support/download/tapo-c200/)). The newest V5
build is 1.5.7 Build 260918 (2026-10-10). It added "selecting specific Activity
Types in notification settings", but no new detection type.

On models that do have it, TP-Link says pet detection "is currently in a beta
testing stage" ([official community article](https://community.tp-link.com/en/smart-home/forum/topic/848428),
posted 2025-11, edited 2026-01).

The C200 is on the "applies to" list of the sound detection FAQ, which includes
a beta Cat Meow Detection. The same FAQ says most indoor cameras only get baby
crying, and the C200 spec pages list only BabyCry
([FAQ 3895](https://www.tp-link.com/us/support/faq/3895/)). A cat on the counter
is quiet anyway.

### Checking your version

In the Tapo app, tap the camera card, then the gear icon, then the camera model.
The page shows Hardware Version and Firmware Version. The hardware version is
also printed on the label under the camera
([FAQ 315](https://www.tp-link.com/en/support/faq/315/)).

## On camera or subscription, and price

Motion and person detection and plain push notifications work without a
subscription. The spec pages list "System Notification" on its own and tag only
"System Notification with Snapshot" and "with Clips" as Tapo Care services
([V5 page](https://www.tp-link.com/en/home-networking/cloud-camera/tapo-c200/)).

Tapo Care does not add detection types. Its current plan table lists cloud
video history, notifications with snapshots, smart sort, video summary, weekly
report and detection-triggered recording
([Tapo Care](https://www.tapo.com/en/tapocare/)). "Smart sort" tags clips by
whatever AI detection the camera already does. An older German Tapo Care page
still says "AI Detection now supports person detection and baby crying
detection" ([DE page](https://www.tp-link.com/de/tapocare/)), so on V1 and V2
person detection may have been a cloud feature.

TP-Link's FAQ no longer prints prices and says the app is authoritative
([FAQ 3408 DE](https://www.tp-link.com/de/support/faq/3408/), updated
2026-10-10). The German App Store listing shows these in-app prices
([App Store DE](https://apps.apple.com/de/app/tp-link-tapo/id1472718009)):

| Plan | Monthly | Yearly |
|---|---|---|
| Basic, 1 camera (7-day history) | 2,99 € | 29,99 € |
| Premium, 1 camera (30-day history) | 3,49 € | 32,99 € |

Each camera gets one 30-day free trial. The German Tapo store listed 3,99 € a
month for one camera in April 2024
([Tapo store DE](https://de.store.tapo.com/blogs/haufig-gestellte-fragen/tagged/tapo-care)),
so prices move. Both are under 5 €.

## Activity zones

Spec pages for V3, V3.20 and V5 say activity zones exist but "Only works with
Motion Detection". Firmware has since widened that:

V3 1.3.13 (2024-04-09) added "separate activity zones for different detection
types" ([V3 notes](https://www.tp-link.com/de/support/download/tapo-c200/v3/)).
V4 1.4.0 (2024-12-31) added any rectangular zone for AI and motion detection
([V4 notes](https://www.tp-link.com/de/support/download/tapo-c200/v4/)).

So a zone over the counter is possible. It is a 2D rectangle in the image,
though. A person standing in front of the counter, or a hand moving a pot on it,
falls inside the same rectangle. TP-Link also warns that diagonal movement can
make a bounding box overlap a zone edge when the subject is outside it
([community article](https://community.tp-link.com/en/smart-home/forum/topic/848428)).

## Notification delay

TP-Link publishes no latency figure. Its troubleshooting FAQ treats delays as a
phone or network problem (Do Not Disturb, Low Power Mode, weak Wi-Fi) and gives
no expected number ([FAQ 4853](https://www.tp-link.com/de/support/faq/4853/),
updated 2026-07-01). The C200 delay threads on the forum are from 2020 and 2021,
on Android with firmware 1.0.x, where Doze held alerts until the phone was
unlocked ([example](https://community.tp-link.com/en/business/forum/topic/257248)).
I found no iPhone measurements. If this route is ever tried, time it.

## False positives and repeat alerts

From TP-Link's own false-detection article
([community](https://community.tp-link.com/en/smart-home/forum/topic/848428)):
motion detection fires on sudden light changes, shadows and insects near the
lens, mostly in night IR mode. Person detection can mistake "pets, lamps, trash
cans" for a person. Detection works best with the subject 1.5 to 5 m away.

Firmware notes for V1 1.3.9 and V3 1.3.5 both say "Fixed the problem of false
person detection in some cases".

For this kitchen the relevant number is simpler: motion detection has no class
at all, so every person who works at the counter inside the zone triggers it.

There is no cooldown setting. A request for "a setting not to renotify within
a selectable period" (Tapo C120, 2024-01-16) got a moderator reply that they
had no details on if or when, and the thread was later locked with no feature
announced ([topic 651160](https://community.tp-link.com/en/home/forum/topic/651160)).
The current notification FAQ covers activity types and a schedule, nothing on
frequency ([FAQ 3742](https://www.tp-link.com/us/support/faq/3742/), updated
2026-10-16).

## Snapshot and iOS priority

Snapshots in notifications need Tapo Care: "Rich Notifications (Tapo Care
Required)" ([FAQ 3742](https://www.tp-link.com/us/support/faq/3742/)).

No TP-Link page mentions Apple's Time Sensitive level. The app does have a
"Critical" notification type, set per Activity Type, which on iOS uses Critical
Alerts: they play a sound even when the phone is muted or in a Focus
([FAQ 806](https://www.tapo.com/us/faq/806/), updated 2026-09-29). That FAQ
names no supported models and its setup line talks about a baby camera. The C200
V5 only got Activity Type selection in firmware 1.5.7, so whether it offers
Critical has to be checked in the app.

## Open points

These were not settled by any source and only matter if the app route is
reconsidered:

1. Whether a C200 on firmware 1.5.7 offers the Critical type.
2. Real push latency on the iPhone.
3. A partial workaround: a motion zone on the counter with a notification
   schedule limited to hours when nobody is in the kitchen. It would still
   alert in bursts and on light changes.
