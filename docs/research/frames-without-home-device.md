# Can frames reach the cloud with no device at home?

Research for #2. Sources checked on 2026-10-19. Numbers marked "estimate" were not measured; check them on the real setup.

## Answer

Not safely with only the camera and TP-Link's cloud. TP-Link offers no way for our code to get frames or events from a C200, and port-forwarding RTSP is unsafe. The one no-home-device path that can be made reasonably safe is a VPN run by the router itself, joined by an always-on cloud VM that pulls RTSP. It depends on the router model and the ISP line, and it hands the cloud VM a way into the home LAN.

Recommendation: keep the Pi 4 as a thin relay that pushes JPEG frames out over HTTPS. Revisit only if the router check below shows Tailscale or a WireGuard client mode with per-device rules.

| Option | Works with C200 | Cat to frame in cloud | Cost per month | Security risk |
|---|---|---|---|---|
| Tapo cloud (Care, IFTTT, Open API) | No frame access for our code | n/a | Care about 3 to 4€ | Low, but unusable |
| Unofficial cloud relay (ontapo) | Untested on C200 | a few seconds per frame | 0€ plus a host | High: undocumented, full account access |
| Router VPN, cloud VM pulls RTSP | Yes | under 1 s (estimate) | 0€ (Oracle free tier) or a paid VM | Medium: VM gets LAN access |
| Port-forward RTSP | Yes | under 1 s (estimate) | 0€ plus a VM | High |
| Pi 4 pushes frames (baseline) | Yes | about 1 s (estimate) | 0€ on Workers free tier | Low: outbound only |

## 1. Tapo's own cloud

Tapo Care keeps event clips in TP-Link's cloud. You view and download them by hand in the Tapo app [3610]. One camera costs about 3 to 4€ a month in Germany; TP-Link's price FAQ shows two tables that disagree, and the app has the final price [3408]. There is no documented API to fetch clips.

IFTTT is gone. TP-Link ended its IFTTT services for Tapo and Kasa, and applets stopped on 2026-08-01 [ifttt]. Even before that, TP-Link staff said in 2020 there was no plan to add IFTTT for Tapo cameras [tp-ifttt].

TP-Link's Open API program targets business partners. Its landing page blocked automated fetches; the search index copy says the cloud-to-cloud API covers smart plugs and not cameras [openapi]. Treat this as unconfirmed.

Alexa and Google Home only show live view on their own screens, capped per session [2680]. I found no API in either that hands frames to our code.

The one unofficial cloud path is `ontapo` 0.1.0 (August 2026) [ontapo]. It logs in with the Tapo account and pulls live video or a snapshot through TP-Link's cloud relay, with no LAN access or camera password. Problems:

- verified only on the C216 and TC65, not the C200;
- built on undocumented endpoints that can break for good at any time, and its author says not to rely on it for alarms;
- TP-Link's terms may forbid third-party clients;
- its saved session gives full access to every camera on the account, so a leak from the cloud host is a leak of the camera;
- `snapshot()` pulls a few seconds of video to decode one frame, so each frame costs seconds.

A missed cat is the worst outcome on this project, so a client that can stop working overnight rules this out.

The Tapo app's own pet detection and push alerts are the only official cloud path for events. Ticket #3 covers them.

## 2. VPN on the router, cloud host pulls RTSP

The router runs a VPN server (WireGuard, or Tailscale as a subnet router). A cloud VM joins it and runs ffmpeg against `stream2` on port 554 [2680].

Cloudflare Workers cannot be that host. `connect()` speaks TCP only and refuses private IPs [cf-tcp]. Workers VPC reaches private networks only through `cloudflared`, a Cloudflare Mesh node (a Linux box running Cloudflare's client), or Cloudflare WAN [cf-vpc] [cf-mesh]. The first two need a device at home, and Cloudflare WAN is enterprise-only [cf-wan]. So this option needs a VM.

Oracle's Always Free tier has 2 Arm OCPUs, 12 GB RAM and 10 TB egress at 0€. Oracle may reclaim an instance that looks idle for 7 days: p95 CPU under 20%, network under 20%, and on Arm shapes memory under 20% [oracle]. A light RTSP puller may well count as idle. Paid VM prices moved in 2026, so check the current price before assuming one fits under 5€.

Whether the router is reachable decides the rest:

- An inbound VPN server needs a public IPv4 or IPv6 address. FRITZ!Box, ASUS and TP-Link all state this [avm] [asus] [tplink-wg].
- Under carrier-grade NAT (router WAN address in 100.64.0.0/10, RFC 6598) an inbound IPv4 VPN cannot work [tplink-wg].
- On a DS-Lite line a FRITZ!Box is reachable over IPv6 only [avm]. The VM would then need IPv6.
- Outbound modes survive CGNAT. Tailscale opens no inbound ports and falls back to an encrypted relay [ts-review] [ts-conn]. GL.iNet routers ship it from firmware 4.2 (beta, listed models only) [glinet]; OpenWrt has packages.

Delay: with the RTSP session held open, the frame reaches the VM after the network round trip plus decode, well under a second (estimate). Opening a new session per frame adds RTSP setup and a wait for the next keyframe. TP-Link does not document the C200's keyframe interval; measure it with `ffprobe`.

Security: a WireGuard server does not answer packets from unknown peers [wg], so the open UDP port itself is a small risk. The larger risk is the cloud VM. It holds a key into the home LAN and the camera account password. Router VPN servers usually give a peer the whole LAN, not one IP and port; check each router. If the VM is taken over, the attacker sits on the camera's network, where most C200 CVEs apply (table below), next to every other home device. Tailscale access rules can narrow the VM to the camera's port 554 [ts-subnet].

## 3. Port-forwarding RTSP

TP-Link's own FAQ says RTSP and ONVIF are not secure enough to leave exposed on a public IP and recommends a VPN [2680]. Other problems:

- TP-Link documents no RTSPS. The video crosses the internet in clear, readable by anyone on the path.
- Whether the C200 uses Basic or Digest auth on RTSP is not documented. Basic sends the password base64-encoded. MD5 Digest lets someone who captures one exchange guess the password offline (RFC 7616, section 5).
- NVD rates most C200 flaws as adjacent-network because the services are meant for the LAN. A port forward puts them on the internet.

C200 CVEs on NVD (keyword "Tapo C200") [nvd]:

| CVE | Hardware | What | Fix |
|---|---|---|---|
| CVE-2021-4045 | v1, fw 1.1.15 and older | Unauthenticated RCE as root in the web server, CVSS 9.8 | 1.1.16 |
| CVE-2025-8065 | v3 | Stack overflow in ONVIF SOAP parser (port 2020), RCE | see TP-Link FAQ 4849 |
| CVE-2025-14300 | v3, v5 | Unauthenticated Wi-Fi reconfiguration over HTTPS | see TP-Link FAQ 4849 |
| CVE-2026-1871 | v5 | Stack overflow in RTSP Authorization header handling, crash and reboot | 1.4.4 Build 260527 [5113] |
| CVE-2026-15315 | v5 | Login bypass to admin session | 1.4.6 |
| CVE-2026-102369 | v5 | Replayed login plus command injection, RCE | see TP-Link FAQ 5321 |

CVE-2026-1871 sits on exactly the port a forward would expose. Verdict: do not port-forward the camera with any router.

## 4. Baseline: Pi 4 as a thin relay

Option A, push (recommended). One `ffmpeg` process holds an RTSP session to `stream2` on the LAN and writes a JPEG every N seconds. A small loop POSTs each JPEG over HTTPS to a Worker. Everything is outbound, so there is no port forward and no VPN, and it works behind CGNAT. The camera password stays on the Pi; the cloud only ever sees frames.

- Delay: under a second to grab, plus the upload (estimate).
- Cost: Workers Free allows 100,000 requests a day and 10 ms CPU each; Workers Paid is $5/month for 10 million requests [cf-price]. One frame a second is 86,400 requests a day, which fits but leaves little room; one every 2 s is 43,200. R2's free tier has 1 million writes a month [cf-price], and one frame a second is 2.6 million, so do not store every frame.
- Upload: a low-res JPEG of about 30 KB a second is about 2.6 GB a day (estimate).
- Pi load: one ffmpeg decoding the low-res stream plus one JPEG encode per sample. Expect a small slice of one core and well under 100 MB RAM (estimate; check with `top`). The detector, the part that sank Frigate, moves to the cloud. `-skip_frame nokey` cuts decoding further if sampling at the keyframe rate is enough.
- Failure watch: frames arrive on a fixed beat, so the cloud can raise an alarm when they stop.
- Motion gating: the C200 exposes ONVIF motion events through PullPoint, but the maintainer of the Home Assistant Tapo integration reports subscription renewals failing on the C200 [ha-tapo]. Use them as a hint at most, not as the only trigger.

Option B, tunnel. The Pi runs Tailscale, `cloudflared` or a Cloudflare Mesh node and exposes the camera's port 554 to the cloud. The Pi does almost nothing, but the cloud needs a VM with ffmpeg again and gets a path into the LAN. No gain over A for this project.

Note: TP-Link says Tapo Care, local recording and NVR/ONVIF recording cannot all run at once for lack of stream resources [2680]. It is unclear whether a plain RTSP pull counts as NVR recording. Do not enable all three, and test.

## What to check

1. Router make, model and firmware version (label and admin page).
2. The WAN address on the router's status page. If it is in 100.64.0.0/10 or a private range, or differs from what a "what is my IP" site shows, the line is behind CGNAT and inbound VPN over IPv4 is out.
3. Whether the line has IPv6, and whether it is DS-Lite.
4. VPN menus: WireGuard or OpenVPN server, WireGuard client, Tailscale. FRITZ!Box needs FRITZ!OS 7.50+ [avm], ASUS firmware newer than 3.0.0.4.388.23000 [asus], TP-Link Archer select newer models [tplink-wg].
5. Whether a VPN peer can be limited to one LAN IP and port.
6. The C200 hardware version (label) and firmware (Tapo app). Update it either way; the CVEs above differ by hardware version.

## Sources

- [2680] TP-Link, RTSP/ONVIF FAQ: https://www.tp-link.com/en/support/faq/2680/
- [3408] TP-Link, Tapo Care pricing: https://www.tp-link.com/it/support/faq/3408/
- [3610] TP-Link, downloading Tapo videos: https://www.tp-link.com/cz/support/faq/3610
- [ifttt] IFTTT, TP-Link Kasa and Tapo service update: https://help.ifttt.com/hc/en-us/articles/54020875164955
- [tp-ifttt] TP-Link community, C200 IFTTT thread: https://community.tp-link.com/en/home/forum/topic/209316
- [openapi] TP-Link Open API landing page: https://tp-link.com/th/landing/open-api
- [ontapo] ontapo on PyPI: https://pypi.org/project/ontapo/
- [nvd] NVD API: https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=Tapo%20C200
- [5113] TP-Link advisory for CVE-2026-1871: https://www.tp-link.com/us/support/faq/5113/
- [cf-tcp] Cloudflare, Workers TCP sockets: https://developers.cloudflare.com/workers/runtime-apis/tcp-sockets/
- [cf-vpc] Cloudflare, Workers VPC: https://developers.cloudflare.com/workers-vpc/
- [cf-mesh] Cloudflare Mesh: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-mesh/
- [cf-wan] Cloudflare WAN: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-wan/
- [cf-price] Cloudflare, Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- [oracle] Oracle, Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- [avm] AVM, WireGuard between FRITZ!Box networks: https://fritz.com/en-at/apps/knowledge-base/FRITZ-Box-6820/3686_Setting-up-a-WireGuard-VPN-between-two-FRITZ-Box-networks
- [asus] ASUS, WireGuard server FAQ: https://www.asus.com/support/faq/1048280/
- [tplink-wg] TP-Link, WireGuard on routers: https://www.tp-link.com/us/support/faq/3772/
- [glinet] GL.iNet, Tailscale: https://docs.gl-inet.com/router/en/4/interface_guide/tailscale/
- [ts-review] Tailscale, reviewer guide: https://tailscale.com/compare/reviewer-guide
- [ts-conn] Tailscale, connection types: https://tailscale.com/docs/reference/connection-types
- [ts-subnet] Tailscale, subnet routers: https://tailscale.com/docs/features/subnet-routers
- [wg] WireGuard protocol, DoS mitigation: https://www.wireguard.com/protocol/
- [ha-tapo] HomeAssistant-Tapo-Control issue 330: https://github.com/JurajNyiri/HomeAssistant-Tapo-Control/issues/330
- RFC 6598 (shared address space for CGNAT), RFC 7616 (HTTP Digest)
