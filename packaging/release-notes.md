## Which file do I download?

| Your computer | Download |
|---|---|
| Mac with Apple silicon (M1 or newer) | the file ending `mac-apple-silicon.dmg` |
| Mac with an Intel processor | the file ending `mac-intel.dmg` |
| Windows 10 or 11 | the file ending `windows-setup.exe` |
| Chromebook, or Debian / Ubuntu Linux | the `.deb` ending `amd64.deb`, or `arm64.deb` for an ARM processor |
| Other Linux | the `.tar.gz` for your processor |

- **Which Mac?** Apple menu → About This Mac. "Chip: Apple M…" means Apple silicon; "Processor: … Intel" means Intel.
- **Which Chromebook?** Settings → About ChromeOS → Diagnostics shows the processor. MediaTek or Qualcomm/Snapdragon means ARM (`arm64.deb`); Intel, AMD or Celeron means `amd64.deb`.

These apps aren't signed with paid developer certificates, so your computer will warn you the first time you open one. The [README](https://github.com/drewsiegler/district-lookup#install) walks through getting past the warning on each system, and through installing on a Chromebook.

To update, download the new version and install it over the old one. Your saved address lookups are kept.

District Lookup is free. If it helps your work, you can [support it on Ko-fi](https://ko-fi.com/andrewsiegler).
