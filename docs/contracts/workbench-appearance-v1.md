# Workbench appearance@1

UI preferences are session configuration; they never enter WB project JSON or image exports.
`session('appearance', {schema_version:1, requestId, values:{theme,density,motion}})`
accepts exactly the three fields. Theme is forest/ember/iris/neutral; density is
comfortable/compact; motion is expressive/gentle/reduced. Request IDs are nonempty,
at most 80 characters. Snapshots contain schema_version, values, configured, receipt,
error. The matching receipt, not the click or animation, acknowledges persistence.

Desktop storage uses workbench_appearance_v1 in release-channel-isolated QSettings.
Other windows refresh at one-second intervals. Invalid stored data is retained;
invalid commands do not alter live values. Failed writes restore the previous value,
report an error and leave live preferences unchanged. The web view previews the choice,
then rolls back on failure. It serializes pending edits and never accepts an older
receipt as acknowledgement of a newer choice. Legacy reduced-motion is migrated only
when there is no configured appearance. System reduced motion always takes priority.

Appearance, scientific values and project revision are independent. The UI resource
tree is identical for preview and desktop; only the bridge adapter changes.
