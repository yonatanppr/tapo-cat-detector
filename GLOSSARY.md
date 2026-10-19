# Cat detector

Watches the kitchen counter through the Tapo C200 and tells the owner when the cat is on it.

## Language

**Counter**:
The kitchen counter surface the camera watches, where food is left out.
_Avoid_: Kitchen, worktop

**Alert**:
A push notification on the owner's iPhone saying the cat is on the counter.
_Avoid_: Notification, alarm

**Sighting**:
A frame the detector judges to show the cat on the counter, rightly or not.
_Avoid_: Detection, hit

**Incident**:
A run of sightings close to one another on the counter, from the first until that spot has been clear long enough. A quick hop down and back up is the same incident; a sighting elsewhere on the counter starts another. Each incident sends one alert.
_Avoid_: Event, episode

**Snooze**:
A pause the owner starts from an alert, during which no alerts are sent. Nothing seen during it carries over, so a cat still on the counter when it ends alerts again.
_Avoid_: Mute

**False alert**:
An alert sent when no cat is on the counter, such as for a person or a pot.
_Avoid_: False positive

**Missed cat**:
A cat on the counter that produced no alert. Worse than a false alert.
_Avoid_: False negative
