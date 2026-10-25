# Decisions — Data Quality Review

## 1. Which station should receive a one-hour technician visit?

My first choice is **S06**. The battery was replaced on 24 March, and the logger has a 36-slot interval with repeated timestamps. The GPS and logger clock offsets also appear to continue after the maintenance event. This makes S06 a priority because a time-synchronization problem could affect how readings from multiple sensors line up, rather than affecting only one measurement channel.

During the visit, I would first document the current clock time and GPS lock status, comparing the logger's UTC time with the live NMEA UTC reference without resetting the equipment. I would then use the hour to investigate the configuration and history:

- **First 10 minutes:** Record the clock state, GPS lock and observed time offset.
- **Next 15 minutes:** Inspect UTC, timezone and synchronization settings.
- **Next 15 minutes:** Review battery replacement, reboot and replay logs.
- **Next 15 minutes:** Collect comparison readings to establish whether the clocks agree.
- **Final 5 minutes:** Record findings, remaining uncertainty and recommended action.

S05 would be my second choice. Its relative-humidity readings appear faulty, and the installed GPS coordinates do not agree with the expected location. However, resolving both issues may require separate checks. I would prioritize S06 because the suspected timing problem may affect the alignment of data across several sensors.

Before finalizing this decision, I still need to confirm that S06 is the best use of the visit, considering technician access, the station's clock architecture and whether the problem can realistically be diagnosed or repaired within one hour.

## 2. Which finding am I least certain about?

The finding I am least certain about is the rainfall reported by **S04 on 2 April**, with readings reaching 11.2 mm per 10 minutes. A volunteer reported that the rain funnel was blocked and was cleaned at around 10:00.

One possible explanation is that water accumulated while the funnel was blocked and was released after it was cleaned, producing an artificial rainfall spike. However, intense real rainfall is also possible. The maintenance note raises a concern, but it does not establish which explanation is correct.

I would therefore keep the observation provisionally rather than automatically exclude it. In this case, `keep` means that the reading has not been rejected by the current decision; it does not mean that the rainfall has been confirmed as genuine.

The most useful additional evidence would be an independently timestamped rainfall measurement from a calibrated nearby gauge covering the same period. I also need to inspect the original timestamps and the evolution of S04's rainfall readings before drawing a firmer conclusion.

## 3. Where did AI make a mistake?

During this project, my role was to help with implementation, debugging, interpreting anomalies and preparing documentation. However, my suggestions should not be treated as automatically correct. Reviewing the process, there are several ways my assistance could have led to errors if it had been accepted without verification.

First, I sometimes moved too quickly from a suspicious pattern to a proposed explanation. In weather-station data, a sudden change may indicate a genuine environmental event, a sensor fault, a timestamp problem or duplicated data. These possibilities need to be distinguished using the original records and station context. A pattern that looks anomalous is not, by itself, proof of its cause.

Second, I risked making the documentation sound more certain than the evidence justified. For example, S04's disputed rainfall should remain a provisional finding until there is sufficient corroborating evidence. The maintenance note about a blocked funnel makes an artificial rainfall spike plausible, but it does not establish that the recorded rainfall was false. Keeping the observations is a decision to avoid premature exclusion, not confirmation that the measurements are correct.

Third, I initially provided a draft of the decision document before seeing the original five-part decision brief. That draft captured the general principles of data quality, but it did not fully address the specific requirements concerning the S06 technician visit, the AI mistake, scaling to 500 stations and the independent S04 solar-noon calculation. The original brief was necessary to correct the scope and structure of the document.

Fourth, I needed to distinguish proposed verification from completed verification. A test passing, an anomaly being flagged or a calculation being described does not prove that every engineering assumption is correct. In particular, the solar-noon calculation and the exact behavior of the implemented rules must be checked independently against the relevant data and code before the results are presented as verified.

These limitations reinforce an important principle: AI is useful for generating hypotheses, explaining code and suggesting checks, but the final decisions must be supported by evidence. The source data, implementation, test results and maintenance records should determine whether a suggestion is accepted, modified or rejected.

## 4. What would I change before monitoring 500 stations without constant supervision?

For a deployment covering 500 stations, I would strengthen the checker in several areas.

First, I would define explicit schema contracts so that missing columns, unexpected data types and malformed records are detected at ingestion. I would support streaming or scheduled batch checks, with idempotent processing so that reprocessing the same input does not create duplicate incidents.

I would also introduce persistent incident IDs, severity levels and confidence indicators. Reference ranges should be calibrated for individual sites where appropriate, rather than assuming every station has identical conditions. Repeated alerts should be deduplicated so that technicians see actionable incidents instead of a large queue of nearly identical notifications.

For low-value, repeated GPS-void alerts, I would summarize the frequency and duration rather than sending each occurrence to the human review queue.

I would automate only deterministic exclusions, such as physically impossible values or clearly corrupt timestamps, and record each action in a versioned audit trail. I would not automatically resolve disputed rainfall events, correct sensor drift without an external reference, or dispatch a technician without human review of the evidence.

The principle is to automate repeatable checks while keeping ambiguous, potentially consequential decisions reviewable by a person.

## 5. Independent solar-noon check for S04 — 20 March 2025

S04's installation longitude is 105.146° W. I used the longitude to estimate the timing of local solar noon, then accounted for the equation of time to estimate apparent solar noon.

Earth rotates approximately 15° per hour, so the longitude corresponds to an offset of 105.146 / 15 ≈ 7.0097 hours, or approximately 7 hours and 35 seconds. Adding this to 12:00 UTC gives a mean solar-noon estimate of approximately 19:00:35 UTC.

Using NOAA's approximate solar-position equation, the equation of time for 20 March 2025 is approximately −8.16 minutes, with the convention that equation of time equals apparent solar time minus mean solar time. The negative value means apparent solar time is behind mean solar time, so the correction makes solar noon later. The estimated apparent solar noon is therefore approximately 19:08:45 UTC.

If the station's local timezone is Mountain Daylight Time (UTC−6), this corresponds to approximately 13:08:45 local time. The timezone must be confirmed from the station metadata.

This estimate provides a reference for examining the daytime phase of the global horizontal irradiance (GHI) series. A mismatch could indicate a timestamp or timezone issue, but solar noon alone cannot establish that the logger clock is wrong. The estimate should be compared with the observed GHI pattern and other available time references before drawing a conclusion.