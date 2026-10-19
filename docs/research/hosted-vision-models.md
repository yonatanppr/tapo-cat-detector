# Hosted vision models for the cat-on-counter check

Research for #4, checked on 2026-10-19 against the pages under Sources. Prices are in USD. The 5€ budget is $5.61 at that day's ECB reference rate of 1.1225 [1].

Frame size assumed throughout: a 640x360 JPEG from the C200's stream2. That size is commonly reported for stream2; confirm it with ffprobe during #6.

## Short answer

- Checking every frame at 0.5 fps (43,200 a day) fits 5€ on two options only: Cloudflare's `@cf/microsoft/resnet-50` inside the free Workers AI allowance (with 1.5% to spare), and YOLO on an Oracle Always Free VM. 1 fps fits only on Oracle.
- Vision LLMs cost 2 to 130 times more per frame than ResNet-50. Within 5€ they cover from a few hundred to about 29,000 frames a day, so they suit a confirm step or motion-gated checks.
- A two-stage setup fits. YOLO on Oracle for every frame plus Clef-flash on the Cloudflare free allowance to confirm costs 0€. An all-Cloudflare two-stage at 0.5 fps does not fit the free allowance, because ResNet-50 alone uses 98.5% of it.
- DETR, named in the ticket, is gone from Workers AI. Its model page returns 404 and it is missing from the catalog index and the pricing page [2][3].
- Nobody publishes image latency for these models. The only figures are vendor text-benchmark numbers for Clef-flash and CPU timings for YOLO26. #8 has to measure it.

## Comparison

| Option | Cost per frame | Frames/day free | Frames/day within 5€ | Published latency | Cat vs person or pot |
|---|---|---|---|---|---|
| CF ResNet-50 | 0.228 neurons ($0.0000025) | 43,800 | 52,000 | none | 5 house-cat labels and several pot labels; no person label; labels the whole image, no location |
| CF Clef-flash, full frame | about 1 neuron ($0.00001) | about 10,000 | about 12,500 | median 39 ms, p95 122 ms (vendor, text) | yes/no probability for any question; no image benchmark |
| CF Clef-flash, 256px crop | about 0.4 neurons | about 24,700 | about 29,000 | same | same, less detail |
| CF Moondream 3.1 `detect` | tokens per image not documented; about 30 neurons if 1,000 | about 340 at that guess | about 400 | none | open-vocabulary boxes, e.g. "cat" |
| Gemini 3.1 Flash-Lite, paid | about $0.00013 | see Gemini section | about 1,400 | none | general vision LLM; boxes on request |
| Oracle A1 + YOLO26 | 0 | CPU-bound, 1 fps or more | same | 39 ms (n), 87 ms (s) on an unnamed CPU; A1 not measured | 80 COCO classes incl. cat, person, bowl, cup; no pot class |

"Within 5€" on Cloudflare means Workers Paid at $5 a month [4] plus the $0.61 left over, which buys about 1,850 neurons a day on top of the free 10,000.

## Cloudflare Workers AI

- Both Workers Free and Workers Paid get 10,000 neurons a day free. Above that, Workers Paid bills $0.011 per 1,000 neurons. Limits reset at 00:00 UTC, and requests past a limit fail with an error [3]. On Workers Free that means checks stop until midnight UTC, which the map's failure watch has to catch.
- Workers Free allows 100,000 Worker requests a day [4], enough for one upload per frame at 1 fps.
- Rate limits are 3,000 requests a minute for image classification, 720 for image-to-text and 300 for text generation [5]. None binds at 1 fps.
- Cloudflare does not train on Workers AI inputs and keeps no inputs or outputs for standard inference [6].

ResNet-50 (`@cf/microsoft/resnet-50`) costs $2.51 per million images, or 228,055 neurons per million [3]. Input is the raw image; output is a list of `{label, score}` [7]. The labels are ImageNet's. They include tabby, tiger cat, Persian, Siamese and Egyptian cat, plus wok, Dutch oven, frying pan, Crock Pot and caldron, but no person [8]. It labels the whole image, so it cannot say where the cat is: it needs a crop of the counter, and a person in the crop gets some unrelated label. 1 fps needs 19,700 neurons a day, which comes to $8.20 a month with Workers Paid.

Clef-flash (`@cf/cloudflare/clef-flash`) is a 9B "decision model" post-trained from Qwen3.5-9B, under Apache-2.0 [9][10]. You send up to 4 images and typed questions (`noul` for yes/no, `choice`, `score`) and get a probability per option back, with no free text [9]. It bills input tokens only, at $0.038 per million (3,455 neurons per million) [3]. An image is resized to multiples of 32 px, scaled up to about 256x256 if smaller, and costs one token per 32x32 block plus 3, capped at 1,024 [9]. So a 640x360 frame is about 223 tokens, and with about 50 tokens of questions, about 1 neuron. The vendor reports a median of 38.8 ms and p95 of 122.4 ms on its own text benchmark [10]; image latency is not published. A probability suits this job: the threshold can sit low because a miss is worse than a false alert, and one call can ask "cat on the counter?", "person?" and "pot?" together.

Moondream 3.1 (`@cf/moondream/moondream3.1-9B-A2B`) is a 9B mixture-of-experts model with 2B active, with tasks `query`, `caption`, `point` and `detect` [11]. `detect` with `target: "cat"` returns boxes that can be checked against a counter polygon. It costs $0.30 per million input tokens and $1.00 per million output [3]. Neither Cloudflare nor the model card says how many tokens an image uses [11][12]. The response's `metrics.input_tokens` reports it, so #8 should log it.

Other image-capable models on Workers AI include Llama 3.2 11B Vision, Llama 4 Scout, Mistral Small 3.1 and several large LLMs [2]. None documents image token counts. Meta's licences for the multimodal Llama 3.2 and Llama 4 models grant no rights to people domiciled in the EU, except as end users of a product built on them [13][14]. Gemma 3 12B was deprecated on 2026-05-30 [15]. I left these off the shortlist because Clef-flash and Moondream answer this kind of question directly for the same price or less.

## Google Gemini API

- The cheapest vision models are Gemini 3.1 Flash-Lite at $0.25 per million input tokens and $1.50 per million output, and Gemini 3.5 Flash-Lite at $0.30 and $2.50 [16]. Thinking tokens bill as output [17].
- A Gemini 3 image costs 280 tokens at `low` media resolution, 560 at `medium` and 1,120 by default [18]. At `low`, with a short prompt and about 30 output tokens, a frame costs about $0.00013, so 5€ buys about 1,400 frames a day.
- Free tier: the rate-limit page no longer lists free-tier numbers and says to look them up per project in AI Studio [19]. Third-party guides quote about 1,000 requests a day for Flash-Lite; I could not confirm that on a Google page. Even at that figure, free covers one frame every 86 s.
- On the free tier Google uses prompts and responses to improve its products, and human reviewers may read them. Users in the EEA, Switzerland or the UK get the paid-tier data terms on free use too. On the paid tier there is no training, and prompts are logged for a limited time for abuse checks [20].
- The terms say the API is for "professional or business purposes, not for consumer use" [20]. A home project is a grey area.
- Gemini can return boxes as `box_2d`, normalised to 0-1000 [21], which allows a counter-zone check.

## Oracle Cloud Always Free VM

- Ampere A1 gets 1,500 OCPU hours and 9,000 GB hours a month, which is 2 OCPUs and 12 GB [22]. Oracle's Arm page still says 3,000 OCPU hours [23]; the Always Free page is the newer source.
- Outbound transfer is 10 TB a month [22].
- Oracle may reclaim an Always Free VM if, over 7 days, 95th-percentile CPU, network and memory use are all under 20% [22]. YOLO26n at 1 fps on 2 cores would likely stay under 20% CPU. A larger model or a higher cadence raises use; check the metrics before relying on it.
- Creating the VM can fail with "out of host capacity" in the home region [22].
- YOLO26 is Ultralytics' current family, released January 2026, under AGPL-3.0 [24][25]. YOLO26n scores 40.9 mAP at 38.9 ms per 640px frame on CPU with ONNX; YOLO26s scores 48.6 mAP at 87.2 ms [26]. Ultralytics does not name the CPU, and there are no A1 numbers.
- COCO's 80 classes include cat, person, bowl, cup, oven, microwave and sink, but no pot [27]. A pot can only come out as a nearby class or a wrong one, which fits the Frigate false alerts. A larger model and the counter-zone check should help; #8 has to show how much.
- Each frame costs nothing, but there is a VM to patch and watch.

## Other options

- AWS Lambda running YOLO26n: the Lambda pricing page lists 1M requests and 400,000 GB-seconds a month free [28], about 33,000 requests a day. The AWS free-tier page does not say whether that stays free for accounts opened after July 2025 [29]. Cold starts are unmeasured.
- Per-image vision APIs cost too much for every frame. Rekognition DetectLabels is $0.001 per image [30], so 5€ buys about 190 a day.
- Not checked: OpenAI, Groq, Hugging Face Inference Providers.

## Two-stage check

| Every frame | Confirm | Fits 5€? |
|---|---|---|
| YOLO26 on Oracle, 1 fps | Clef-flash, CF free | Yes, 0€, up to about 10,000 confirms a day |
| YOLO26 on Oracle, 1 fps | Gemini 3.1 Flash-Lite, paid | Yes, about 1,400 confirms a day for 5€ |
| ResNet-50 on a counter crop, 0.5 fps, CF | Clef-flash | Only on Workers Paid: about 2,000 confirms a day for about 5€ |
| Clef-flash alone, motion-gated | none | Yes, free, while checks stay under about 10,000 a day |

The confirm step only runs when the first stage sees a cat-like hit and no incident is open, so its volume should be small. It can also veto a real cat. Since a miss is worse than a false alert, either alert on the first stage and let the confirm step suppress only clear person or pot hits, or keep the confirm threshold low. Each stage adds latency, and the measured sum has to stay within 1-2 s.

## Shortlist for #8

1. YOLO26n and YOLO26s, run locally with Ultralytics as they would run on A1: `pip install ultralytics`, then `YOLO("yolo26n.pt")(frame, classes=[15, 0, 45, 41])` for cat, person, bowl and cup. Export to ONNX to time CPU inference.
2. Clef-flash: `POST https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/cloudflare/clef-flash` with `{"model": "clef-flash", "state": "Kitchen camera frame", "images": ["data:image/jpeg;base64,..."], "questions": {"cat_on_counter": {"type": "noul", "instructions": "Is a cat on the kitchen counter?"}}}` [9]. Add `person` and `pot` questions in the same call.
3. Moondream 3.1: same endpoint with `@cf/moondream/moondream3.1-9B-A2B` and `{"task": "detect", "target": "cat", "image": "data:image/jpeg;base64,..."}`. Log `metrics.input_tokens` to get the real cost [11].
4. Gemini 3.1 Flash-Lite: `POST https://generativelanguage.googleapis.com/v1beta/interactions` with header `x-goog-api-key`, body `{"model": "gemini-3.1-flash-lite", "input": [{"type": "text", "text": "..."}, {"type": "image", "data": "<base64>", "mime_type": "image/jpeg", "resolution": "low"}], "generation_config": {"thinking_level": "minimal"}}` [18][21][31]. Use a paid key so frames are not used for training.

ResNet-50 is cheap to add as a fifth once a counter crop exists. Keep API keys in environment variables, never in the repo.

## Recommendation

My pick, pending #8: YOLO26 on an Oracle A1 VM for every frame, with Clef-flash on the Cloudflare free allowance as the confirm step. It is the only setup that runs at 1 fps for 0€. YOLO gives boxes for the counter-zone check, Clef-flash gives a tunable probability and asks about people and pots in the same call, and neither the VM nor Cloudflare trains on the frames. The costs are a VM to maintain, the reclamation rule, and two providers in the path.

If you would rather not run a VM, Clef-flash alone on Cloudflare with motion gating is the simplest option, free up to about 10,000 frames a day. Which one fits also depends on #2 (how frames leave the house) and the cadence decision. The decision is yours, in #9.

## Sources

1. ECB euro reference rates, 2026-10-19: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
2. Workers AI model index: https://developers.cloudflare.com/workers-ai/llms.txt
3. Workers AI pricing, updated 2026-10-19: https://developers.cloudflare.com/workers-ai/platform/pricing/
4. Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
5. Workers AI limits: https://developers.cloudflare.com/workers-ai/platform/limits/
6. Workers AI data usage: https://developers.cloudflare.com/workers-ai/platform/data-usage/
7. ResNet-50 on Workers AI: https://developers.cloudflare.com/workers-ai/models/resnet-50/
8. ImageNet labels (`id2label`): https://huggingface.co/microsoft/resnet-50/blob/main/config.json
9. Clef-flash on Workers AI: https://developers.cloudflare.com/workers-ai/models/clef-flash/
10. Clef-flash model card: https://huggingface.co/Cloudflare/clef-flash
11. Moondream 3.1 on Workers AI: https://developers.cloudflare.com/workers-ai/models/moondream3.1-9B-A2B/
12. Moondream 3 model card: https://huggingface.co/moondream/moondream3-preview
13. Llama 3.2 acceptable use policy: https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/USE_POLICY.md
14. Llama 4 acceptable use policy: https://github.com/meta-llama/llama-models/blob/main/models/llama4/USE_POLICY.md
15. Workers AI changelog: https://developers.cloudflare.com/workers-ai/changelog/
16. Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
17. Gemini thinking: https://ai.google.dev/gemini-api/docs/thinking
18. Gemini media resolution: https://ai.google.dev/gemini-api/docs/media-resolution
19. Gemini rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
20. Gemini API additional terms: https://ai.google.dev/gemini-api/terms
21. Gemini image understanding: https://ai.google.dev/gemini-api/docs/image-understanding
22. OCI Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
23. OCI Arm-based compute: https://docs.oracle.com/en-us/iaas/Content/Compute/References/arm.htm
24. Ultralytics models: https://docs.ultralytics.com/models/
25. Ultralytics licence: https://github.com/ultralytics/ultralytics/blob/main/LICENSE
26. YOLO26: https://docs.ultralytics.com/models/yolo26/
27. COCO class list: https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml
28. AWS Lambda pricing: https://aws.amazon.com/lambda/pricing/
29. AWS Free Tier: https://aws.amazon.com/free/
30. Amazon Rekognition pricing: https://aws.amazon.com/rekognition/pricing/
31. Gemini 3.1 Flash-Lite model page: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite
