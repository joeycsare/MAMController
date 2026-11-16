# MyAnonamouse API Reference

Cleaned and structured from the supplied MAM API documentation copy (`mamapi.txt`).

> **Authentication**
> Use a valid MAM session cookie (`mam_id`) created under **Preferences -> Security**. This reference intentionally contains no email/password login workflow.
>
> *Not in source:* `mamapi.txt` only says "valid session cookie". The cookie name `mam_id` and its creation path are added from outside the source.

> **Source fidelity**
> - `mamapi.txt` names HTTP methods only for the search endpoint (GET and POST). GET for all other endpoints is an assumption.
> - Statements marked *(inference)* or *(not in source)* are additions, not documented behaviour.
> - Contradictions inside the source are collected under [Known source inconsistencies](#known-source-inconsistencies) and are not silently resolved.

## Contents

1. [`GET /jsonLoad.php`](#get-jsonloadphp)
2. [`GET|POST /tor/js/loadSearchJSONbasic.php`](#getpost-torjsloadsearchjsonbasicphp)
3. [`GET /json/bonusBuy.php`](#get-jsonbonusbuyphp)
4. [`GET /tor/download.php`](#get-tordownloadphp)
5. [`GET /json/userBonusHistory.php`](#get-jsonuserbonushistoryphp)
6. [Known source inconsistencies](#known-source-inconsistencies)
7. [Automation constraints](#automation-constraints)
8. [Controller implementation notes](#controller-implementation-notes)

---

## GET `/jsonLoad.php`

Loads current user data without a full page load.

> Method not stated in source (GET assumed).

### Query parameters

| Parameter | Type | Notes |
|---|---|---|
| `clientStats` | empty | If set and `id` is not set, includes client list, torrent counts, and connectable status. 30-minute cache. |
| `id` | int | User ID whose data should be returned. |
| `notif` | empty | If set and `id` is not set, includes notifications. |
| `pretty` | empty | If set and `id` is not set, enables JSON pretty printing. |
| `snatch_summary` | empty | If set and `id` is not set, includes the basic torrent breakdown from the snatch summary. |

The source does not document the structure of the `clientStats` or `snatch_summary` output.

### Output fields

| Field | Type | Description |
|---|---|---|
| `classname` | string | User class name. |
| `downloaded` | string | Formatted downloaded amount. |
| `notifs` | associative array | User notifications. |
| `ratio` | string | Upload/download ratio. |
| `seedbonus` | int | Bonus points / karma / seed bonus when viewing self. |
| `uid` | string | User ID. |
| `uploaded` | string | Formatted uploaded amount. |
| `username` | string | Username. |
| `vip_until` | datetime | VIP expiry when viewing self and the account is VIP. |

### Example (illustrative, not in source)

```http
GET /jsonLoad.php?snatch_summary
Cookie: mam_id=<session-id>
Accept: application/json
```

---

## GET|POST `/tor/js/loadSearchJSONbasic.php`

Searches torrents and returns JSON results instead of HTML. The endpoint accepts GET as well as POST bodies encoded as XML, JSON, multipart form data, or URL-encoded form data.

### Top-level parameters

| Parameter | Type | Notes |
|---|---|---|
| `description` | empty | Return the torrent's full description field. |
| `dlLink` | blank | Return the user-specific download hash in `dl`. To download without a session cookie, prepend `https://www.myanonamouse.net/tor/download.php/` to the hash and append `?tid=<id>`. With a session cookie, use `https://www.myanonamouse.net/tor/download.php?tid=<id>` instead. |
| `isbn` | set | Return the ISBN field (often blank). |
| `mediaInfo` | set | Return the key parts of the media info. |
| `my_snatched` | exists | Restrict results to torrents you have snatched. |
| `perpage` | int | Number of results, from 5 to 1000. |
| `tor` | array | **Required.** Search parameters. |

### Parameters seen only in the source's example inputs

These appear in the example requests but have no entry in the source's parameter tables. Their meaning is not documented.

| Parameter | Where | Example value |
|---|---|---|
| `tor[browseStart]` | URL-encoded example | `true` |
| `tor[browseFlagsHideVsShow]` | JSON example | `"0"` |
| `bannerLink` | URL-encoded example | (empty) |
| `bookmarks` | URL-encoded example | (empty) |
| `thumbnail` | JSON example, top level | `"true"` |

### `tor` parameters

| Parameter | Type | Notes |
|---|---|---|
| `browse_lang` | list[int] | Language IDs to include. |
| `cat` | list[int] | Category IDs to include. |
| `endDate` | date | Latest creation date, exclusive. `YYYY-MM-DD` or Unix timestamp. |
| `hash` | hex string | Hexadecimal-encoded hash of a torrent. The source does not say which hash. |
| `id` | int | Return a single torrent ID. |
| `main_cat` | array | Main category IDs, listed below. |
| `searchIn` | enum | Search area. The source marks the value list as "list to come". Values that appear in the source: `torrents` (JSON example), `myReseed`, `allReseed`, `Bookmarks` (named in the `default` sort rules). The complete list is unknown. |
| `searchType` | enum | Torrent-state filter, listed below. |
| `sortType` | enum | Sort mode, listed below. |
| `srchIn` | array | Fields included in the text search, listed below. |
| `startDate` | date | Earliest creation date, inclusive. `YYYY-MM-DD` or Unix timestamp. |
| `startNumber` | int | Number of entries to skip for pagination. |
| `text` | text | Search text. |

### Main categories

| ID | Category |
|---:|---|
| 13 | AudioBooks |
| 14 | E-Books |
| 15 | Musicology |
| 16 | Radio |

### Search types

| Value | Meaning |
|---|---|
| `all` | Search everything. |
| `active` | Last update had one or more seeders. |
| `inactive` | Last update had zero seeders. |
| `fl` | Freeleech torrents. |
| `fl-VIP` | Freeleech or VIP torrents. |
| `VIP` | VIP torrents. |
| `nVIP` | Torrents that are not VIP. |
| `nMeta` | Torrents missing metadata (old torrents). |

### Search fields (`srchIn`)

If a field is given, `tor[text]` is searched in it. The JSON example passes an array of strings, e.g. `["title", "author", "narrator"]`.

* `author`
* `description`
* `filenames`
* `fileTypes`
* `narrator`
* `series`
* `tags`
* `title`

### Sort types

| Value | Meaning |
|---|---|
| `titleAsc` | Title, descending according to the source description (see [inconsistencies](#known-source-inconsistencies)). |
| `titleDesc` | Title, ascending according to the source description (see [inconsistencies](#known-source-inconsistencies)). |
| `fileAsc` | Number of files, ascending. |
| `fileDesc` | Number of files, descending. |
| `sizeAsc` | Torrent size, ascending. |
| `sizeDesc` | Torrent size, descending. |
| `seedersAsc` | Seeders, ascending. |
| `seedersDesc` | Seeders, descending. |
| `leechersAsc` | Leechers, ascending. |
| `leechersDesc` | Leechers, descending. |
| `snatchedAsc` | Times snatched, ascending. |
| `snatchedDesc` | Times snatched, descending. |
| `dateAsc` | Date added, ascending. |
| `dateDesc` | Date added, descending. |
| `bmkaAsc` | Bookmark date, ascending. May return odd results when not bookmarked. |
| `bmkaDesc` | Bookmark date, descending. May return odd results when not bookmarked. |
| `reseedAsc` | Reseed-request date, ascending. May return odd results when there is no reseed request. |
| `reseedDesc` | Reseed-request date, descending. May return odd results when there is no reseed request. |
| `categoryAsc` | Category number ascending, then title ascending. |
| `categoryDesc` | Category number descending, then title ascending. |
| `random` | Random. |
| `default` | With a text search: weight descending, then ID descending. Otherwise, if `searchIn` is `myReseed` or `allReseed`: same as `reseedAsc`. Otherwise, if `searchIn` is `Bookmarks`: same as `bmkaDesc`. Otherwise: same as `dateDesc`. |

### JSON request example

```json
{
  "tor": {
    "text": "collection cookbooks food test kitchen",
    "srchIn": ["title", "author", "narrator"],
    "searchType": "all",
    "searchIn": "torrents",
    "cat": ["0"],
    "browseFlagsHideVsShow": "0",
    "startDate": "",
    "endDate": "",
    "hash": "",
    "sortType": "default",
    "startNumber": "0"
  },
  "thumbnail": "true"
}
```

### URL-encoded request example

```text
tor%5Bcat%5D%5B%5D=0&tor%5BsortType%5D=default&tor%5BbrowseStart%5D=true&tor%5BstartNumber%5D=0&bannerLink&bookmarks&dlLink&description&tor%5Btext%5D=mp3%20m4a
```

### Result fields

The `data` property is a list of torrent objects. Field table as given in the source:

| Field | Type | Description |
|---|---|---|
| `added` | datetime | UTC upload time. |
| `author_info` | string | JSON object containing author ID/name pairs. |
| `bookmarked` | datetime/null | Bookmark time or null. |
| `browseflags` | bitfield | Bit field of the tags and flags on a torrent. |
| `cat` | string | HTML category display according to user preferences. |
| `category` | int | Specific category ID. |
| `catname` | string | Category name. |
| `comments` | int | Number of comments. |
| `dl` | string | User-specific download hash. Append it to `/tor/download.php/`, plus `?tid=<id>` (see `dlLink`). |
| `filetypes` | string | Concatenated file types. |
| `fl_vip` | boolean | Whether the torrent is freeleech and/or VIP. |
| `free` | boolean | Freeleech status. |
| `id` | int | Torrent ID. The torrent page is `/t/{id}`. |
| `lang_code` | string | Three-letter ISO language code. |
| `language` | int | Internal language ID. |
| `leechers` | int | Number of leechers. |
| `main_cat` | int | Main category ID (13 AudioBooks, 14 E-Books, 15 Musicology, 16 Radio). |
| `my_snatched` | boolean | Whether you have snatched it. Update may lag 5-20 minutes. |
| `narrator_info` | string | JSON object containing narrator ID/name pairs. |
| `numfiles` | int | Number of files. |
| `owner` | int | Uploader user ID. |
| `owner_name` | string | Uploader username. |
| `personal_freeleech` | boolean | Whether you bought it as personal freeleech. Update may lag 5-20 minutes. |
| `seeders` | int | Number of seeders. |
| `series_info` | string | JSON object containing series ID and name/number pairs. |
| `size` | string | Size of the torrent. The source example is a string of decimal digits, e.g. `"6324306932"`. Unit not stated. |
| `tags` | string | Tags. |
| `times_completed` | int | Number of users who fully snatched the torrent. |
| `title` | string | Title. See the `name` conflict below. |
| `vip` | boolean | Whether the torrent is VIP. |
| `total` | int | Results loaded by the server; expands as later pages are requested. (Top-level, next to `data`.) |
| `total_found` | int | Total search results found. (Top-level, next to `data`.) |

Keys that appear in the source's **example output** but not in its field table:

| Key | Example value | Note |
|---|---|---|
| `name` | `"Love at Stake series"` | Appears where the field table says `title`. |
| `filetype` | `"m4a mp3"` | Singular; the field table says `filetypes`. |
| `w` | `"5527"` | Undocumented. Possibly the text-search weight *(inference)*. |
| `description` | BBCode text | Returned when the `description` parameter is set. Not in the output table. |

### Example response fragment

Taken from the source example. `narrator_info` is shortened to two entries and `description` and `dl` are omitted. The source example is itself truncated and contains no `seeders` or `leechers`.

```json
{
  "data": [
    {
      "id": "273200",
      "language": "1",
      "main_cat": "13",
      "category": "108",
      "catname": "Audiobooks - Urban Fantasy",
      "size": "6324306932",
      "numfiles": "149",
      "vip": "0",
      "free": "0",
      "fl_vip": "0",
      "name": "Love at Stake series",
      "w": "5527",
      "tags": "Love at Stake series unabridged 64–128 Kbps Fiction Paranormal Romance Fantasy Vampires Bestseller mp3 m4a",
      "author_info": "{\"8234\": \"Kerrelyn Sparks\"}",
      "narrator_info": "{\"1\": \"Abby Craden\", \"1220\": \"Deanna Hurst\"}",
      "series_info": "{\"67\": [\"Love at Stake\", \"01-16, 13.5\"]}",
      "filetype": "m4a mp3",
      "bookmarked": null
    }
  ]
}
```

---

## GET `/json/bonusBuy.php`

Backend for the bonus-points store. Full URL in the source: `https://www.myanonamouse.net/json/bonusBuy.php`.

> Method not stated in source (GET assumed). The source documents no response body; it only says the call errors when buying less than 50 GiB or more than is affordable.

### Parameters

| Parameter | Type | Requirement / Notes |
|---|---|---|
| `spendtype` | string | **Required.** One of `VIP`, `upload`, `wedges`, `gift`, `sendWedge`. |
| `amount` | int/string | Required for `spendtype=upload`. Integer 50 or higher, or the exact string `Max Affordable ` including the trailing space. Buying less than 50 GiB or more than affordable returns an error. |
| `duration` | int/string | Required with `spendtype` VIP (the source writes `spendtype=vip`). Via the API only `max` is accepted. It fills VIP up to the 90-day limit and buys a minimum of 7 days / 604800 seconds. |
| `giftTo` | int/string | User ID or username for `gift` or `sendWedge`. |

No parameters are documented for `wedges`.

### Automation statements in the source

| `spendtype` | What the source says |
|---|---|
| `gift` | **May not be automated.** May only be run as a single call or batch process from direct user input via user scripts. |
| `sendWedge` | **May not be automated.** Same wording as `gift`. |
| `upload` | No statement about automation. |
| `VIP` | No statement about automation. |
| `wedges` | No statement about automation; no parameters documented. |

The source forbids automating only `gift` and `sendWedge`. Whether `upload` and `VIP` are *permitted* for automation is not stated. Keeping them opt-in is a project policy (see [Automation constraints](#automation-constraints)).

---

## GET `/tor/download.php`

Downloads a torrent file. Requires a valid session cookie.

> Method not stated in source (GET assumed).

### Parameters

| Parameter | Type | Notes |
|---|---|---|
| `tid` | int | **Required.** Torrent ID. |
| `fl` | empty | If set, tells the backend to spend a freeleech wedge to make the torrent personal freeleech (if not already). It will even spend a wedge on VIP torrents. No refund is available. |

### Example

```http
GET /tor/download.php?tid=273200
Cookie: mam_id=<session-id>
```

### Download via hash (without session cookie)

The search endpoint returns a user-specific hash in `dl` when `dlLink` is set. Per the source, a client without a session cookie can prepend `https://www.myanonamouse.net/tor/download.php/` to that hash and append `?tid=<id>`:

```text
https://www.myanonamouse.net/tor/download.php/<dl-hash>?tid=<id>
```

The source does not say whether `fl` is accepted on this route.

> **Automation caution:** Do not set `fl` unless spending a freeleech wedge is explicitly intended. The source warns: "Automation users beware, no refunds available."

---

## GET `/json/userBonusHistory.php`

Returns bonus-point and freeleech-wedge transaction history.

> Method not stated in source (GET assumed).

### Parameters

| Parameter | Type | Notes |
|---|---|---|
| `other_userid` | int | User ID of the other side of the transaction for gifts (points or wedges). |
| `type` | list | Transaction types to include. |

Documented `type` values:

* `giftPoints`
* `giftWedge`
* `wedgePF`
* `wedgeGFL`
* `torrentThanks`
* `millionaires`

### Form-encoded example

```text
type[]=giftWedge&type[]=wedgePF&type[]=wedgeGFL
```

### Example response

The source documents no output field table, only this example. Note that `title` is a number in the first entry and a string or null in the others.

```json
[
  {
    "timestamp": 1644804607.0994999,
    "amount": -1,
    "type": "wedgePF",
    "tid": 330896,
    "title": 1984,
    "other_userid": null,
    "other_name": null
  },
  {
    "timestamp": 1641914230.1078,
    "amount": -1,
    "type": "giftWedge",
    "tid": null,
    "title": null,
    "other_userid": 192566,
    "other_name": "pezzap7"
  },
  {
    "timestamp": 1610486584.1027,
    "amount": -10,
    "type": "wedgeGFL",
    "tid": 220870,
    "title": "Asimov's Robot, Empire, and Foundation Series",
    "other_userid": null,
    "other_name": null
  }
]
```

---

## Known source inconsistencies

These are contradictions or gaps inside `mamapi.txt`. They are preserved here, not resolved. Verify against a real API response before relying on them.

1. **`titleAsc` / `titleDesc`:** The source describes `titleAsc` as "Descending order" and `titleDesc` as "Ascending order", which contradicts the names.
2. **`title` vs `name`, `filetypes` vs `filetype`:** The field table lists `title` and `filetypes`. The example output uses `name` and `filetype` (and an undocumented `w`). Do not hard-require `title`.
3. **Types:** The field table says `boolean` / `int`, but the example output returns strings (`"vip": "0"`, `"id": "273200"`, `"numfiles": "149"`). Parse leniently.
4. **`searchIn`:** Declared as an enum with "list to come". The complete value list is unknown.
5. **`spendtype` casing:** The option list says `VIP`, the `duration` note says `spendtype=vip`. Case sensitivity is unverified.
6. **Methods:** Only the search endpoint names HTTP methods.
7. **Parameters without documentation:** `tor[browseStart]`, `tor[browseFlagsHideVsShow]`, `bannerLink`, `bookmarks`, `thumbnail` appear only in examples.

---

## Automation constraints

### What the source says

* `gift` and `sendWedge` may not be automated. They may only be run as a single call or batch process from direct user input via user scripts.
* The `fl` download parameter spends a freeleech wedge, also on VIP torrents, without refund.
* The source says nothing about automating `upload`, `VIP` or `wedges`.

### Project policy for the controller (not from the source)

Keep the automated feature set limited to operations covered by the supplied API documentation.

**Reads and downloads:**

* Read current user/account data through `/jsonLoad.php`.
* Read the snatch summary using the `snatch_summary` parameter.
* Search torrents through `/tor/js/loadSearchJSONbasic.php`.
* Download selected torrents through `/tor/download.php` with a valid `mam_id` session, without `fl`.
* Read bonus history through `/json/userBonusHistory.php`.

**Opt-in only (source is silent on automation; disabled by default):**

* Buy upload credit through `/json/bonusBuy.php`.
* Buy/extend VIP through `/json/bonusBuy.php`.

**Do not implement:**

* Automated/headless username/password login. This reference uses only a pre-created `mam_id` session.
* Automated `gift` operations (forbidden by the source).
* Automated `sendWedge` operations (forbidden by the source).
* Implicit use of the `fl` download parameter. A freeleech wedge must not be spent accidentally.
* `spendtype=wedges`: no parameters are documented, so it is out of scope.

---

## Controller implementation notes

Points derived from the supplied API contract, useful for implementation and CI tests. Items marked *(project policy)* or *(inference)* are not stated in the source.

1. Treat MAM authentication as a session-cookie dependency, not a username/password login flow.
2. Validate `/jsonLoad.php?snatch_summary` before allowing automated work to proceed *(project policy)*.
3. Parse search result `size` as an integer, e.g. `int("6324306932")`. The unit is presumably bytes *(inference from the example)*.
4. For an audiobook-only search, set `tor[main_cat]` to `[13]`.
5. Keep `gift` and `sendWedge` entirely outside unattended automation.
6. Keep torrent-download wedge spending opt-in; do not add `fl` by default.
7. Keep `BUY_UPLOAD` and `BUY_VIP` disabled by default *(project policy; the source does not mention automation of these operations)*.
8. Parse result objects leniently: do not require `title` (the source example uses `name`), and accept strings for numeric and boolean-like fields.
