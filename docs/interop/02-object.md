# Object body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects, position body |
| Values | [docs/legacy/11-values-object.md](../legacy/11-values-object.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the object body of a record. The decoder gives it for
an Object report and for an Item report. The conventions of
[01-record](01-record.md) apply: the modes, the value objects, the
provenance and the notes.

## 2. Uses

**[agreed]** A record of an Object or of an Item has two uses. `uses` is
`["object", "position"]`. The body `object` gives the name and the state.
The body `position` is the position body of
[01-record section 7](01-record.md#7-position-body), without change.

Thus a comparison of positions reads the same body for a position report,
for Mic-E, for an Object and for an Item.

An alternative was one body for each legacy format, with the position
inside the object body. The author prefers one position body for all
formats.

**[proposed]** The record has both bodies if the identifier is `obj.dti`,
`item.dti` or `wx.obj`. `format` tells an Object from an Item. The object body has
no member for this difference.

## 3. Fields

**[proposed]** The object body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `name` | Bytes | The name. For an Object, without the padding. | `val.obj.name`, `val.item.name` |
| `live` | Flag | `true` for a live Object or Item. `false` for a killed one. | `val.obj.state`, `val.item.state` |

**[proposed]** If the packet ends before a token, the field is a no-value
object, as [01-record section 4.2](01-record.md#42-value-objects) says.

**[agreed]** The name has these cases:

- An Object name of nine `SP` bytes has the effect `computable`. In
  permissive mode, `name` is the empty byte string, with a mark.
- An Item name of fewer than 3 bytes or of more than 9 bytes has the
  effect `computable`. In permissive mode, `name` has all bytes of the
  token, with a mark.

## 4. Position body and report time

**[proposed]** The position body of an Object or an Item has no
`messaging` field. These formats have no messaging flag.

**[agreed]** `report_time` follows
[01-record section 6](01-record.md#6-report-time). If an Object has no
timestamp, `form` is `"received"`. The record then has the note
`amb.val.objtime` on `report_time`. The same applies to an Item.

**[proposed]** If an Object ends before its position, the record does not
show whether the Object has a timestamp. `report_time` is then a no-value
object.

**[agreed]** If the timestamp of an Object has a `syntax` finding, the
finding concerns every field of the position body
([11-values-object section 4](../legacy/11-values-object.md#4-timestamp)).
It does not concern `name` and `live`.

**[proposed]** If a killed Object or Item has position tokens, the
position body gives their values. A reader that wants only live objects
tests `live`.

## 5. Tokens with no value rule

**[proposed]** These tokens of an Object or an Item are in `undecoded`:

- the area descriptor (`ext.area` and its children);
- storm data.

A frequency in the comment gives the frequency body
([07-frequency](07-frequency.md)).

A weather report on an Object or an Item also has the weather body
([03-weather](03-weather.md)). A record of the obsolete Object format has
no body yet.

## 6. Example

The line is the first Object example of APRS12c, p. 76/58. The record is
in strict mode. The input gives no received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001:;LEADER   *092345z4903.50N/07201.75W>088/036",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["object", "position"], "format": "obj.dti", "verdict": "conform", "findings": [],
 "report_time": {"form": "dhm", "day": 9, "hour": 23, "minute": 45, "zone": "utc", "from": [["time.dhm", 25, 32]]},
 "object": {
  "name": {"bytes": "LEADER", "from": [["obj.name", 15, 24]]},
  "live": {"flag": true, "from": [["obj.state", 24, 25]]}},
 "position": {
  "lat": {"v": 49.05833333333333, "res": 0.00016666666666666666, "from": [["lat", 32, 40]]},
  "lon": {"v": -72.02916666666667, "res": 0.00016666666666666666, "from": [["lon", 41, 50], ["lat", 32, 40]]},
  "ambiguity": {"code": 0, "from": [["lat", 32, 40]]},
  "datum": {"code": "default", "from": []},
  "course": {"v": 88, "res": 1, "from": [["ext.csespd", 51, 58]]},
  "speed": {"v": 66.672, "res": 1.852, "from": [["ext.csespd", 51, 58]]},
  "symbol": {"chars": "/>", "classic": 29, "from": [["sym.table", 40, 41], ["sym.code", 50, 51]]},
  "extensions": []},
 "notes": [["amb.val.datum", "position.datum"]],
 "undecoded": []}
```

The values are derived as follows:

- `lat`: 49° 03.50' N is 49 + 3.5 / 60 degrees. `res` is 1 / 6000 degree.
- `lon`: 72° 01.75' W is −(72 + 1.75 / 60) degrees.
- `speed`: 36 knots × 1.852 is 66.672 km/h. `res` is 1.852 km/h.
- `classic`: the code `'>'` is 0x3E. In the primary table, the number is
  0x3E − 33 = 29.

## 7. Open items

- **[open]** Whether the object body also names the station that reports
  the Object. `source` of the envelope gives the sender of the packet.
  Any station can take over an Object by its name (p. 75/57).
- **[open]** The values of the area descriptor, the corridor and the
  signpost.
- **[open]** A record of the obsolete Object format.
