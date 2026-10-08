## Which file do I download?

| Your computer | Download |
|---|---|
| Mac with Apple silicon (M1 or newer) | the file ending `mac-apple-silicon.dmg` |
| Mac with an Intel processor | the file ending `mac-intel.dmg` |
| Windows 10 or 11 | the file ending `windows-setup.exe` |
| Chromebook, or Debian / Ubuntu Linux, with an Intel or AMD processor (most Chromebooks) | the file ending `_amd64.deb` |
| Chromebook, or Debian / Ubuntu Linux, with an ARM processor (MediaTek, Qualcomm Snapdragon) | the file ending `_arm64.deb` |
| Other Linux | the `.tar.gz` ending `amd64` (Intel or AMD) or `arm64` (ARM) |

- **Which Mac?** Apple menu → About This Mac. "Chip: Apple M…" means Apple silicon; "Processor: … Intel" means Intel.
- **Which Chromebook?** The two `.deb` files are the same app built for two kinds of processor, and only the right one installs. Settings → About ChromeOS → Diagnostics shows the processor: Intel, AMD, Celeron or Pentium means `_amd64.deb`; MediaTek or Qualcomm Snapdragon means `_arm64.deb`.

These apps aren't signed with paid developer certificates, so your computer will warn you the first time you open one. The [README](https://github.com/drewsiegler/district-lookup#install) walks through getting past the warning on each system, and through installing on a Chromebook.

To update, download the new version and install it over the old one. Your saved address lookups are kept.

District Lookup is free. If it helps your work, you can [support it on Ko-fi](https://ko-fi.com/andrewsiegler).
