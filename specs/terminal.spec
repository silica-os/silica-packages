# prepare: flutter .

%global srcrepo terminal
%global commit 37e4047073e4f746fb0ef4522cef8c09c87a92ad
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20261019
%global appid dev.frascella.Terminal

# Nothing is compiled by rpmbuild (the Dart AOT library comes prebuilt, docs/flutter.md):
# no debuginfo.
%global debug_package %{nil}
# The Dart AOT library is private (dlopen'ed by the embedder).
%global __provides_exclude_from ^%{_prefix}/Applications/.*$

Name:           terminal
Version:        0^%{snapdate}git%{shortcommit}
Release:        1%{?dist}
Summary:        Terminal emulator of Silica

# Terminal: MIT OR Apache-2.0; the Dart packages linked in libapp.so are listed in
# flutter_assets/NOTICES.Z. JetBrains Mono (OFL-1.1) is bundled in the assets.
License:        (MIT OR Apache-2.0) AND OFL-1.1 AND LicenseRef-Bundled-Dart
URL:            https://github.com/silica-os/terminal
Source0:        %{srcrepo}-%{commit}.tar.gz
Source1:        %{srcrepo}-%{commit}-dart-root.tar.zst

ExclusiveArch:  x86_64
BuildRequires:  zstd
BuildRequires:  desktop-file-utils
# silica-bundle puts the app bundle together (silica-os docs/app-bundles.md).
BuildRequires:  silica-apps

Requires:       silica-embedder%{?_isa}
Requires:       silica-apps
Recommends:     silica-icons

%description
Terminal is Silica's terminal emulator: tabs, profiles and split panes. The
pseudo-terminal lives in the Silica embedder (silica/pty channel).

%prep
%autosetup -n %{srcrepo}-%{commit}
mkdir bundle
zstd -dc %{SOURCE1} | tar -x -C bundle

%build
# Built ahead of time by tools/container.sh (Dart AOT, see docs/flutter.md).

%install
# Terminal as an app bundle in /usr/Applications (silica-os#3, silica-os docs/app-bundles.md): a
# system app, allowed by its folder and run without a sandbox. Signing with the release key
# happens where the key is available (silica-bundle build --key); without it the bundle is
# unsigned.
version=$(sed -n 's/^version: *\([^+ ]*\).*/\1/p' pubspec.yaml)
install -dm 0755 %{buildroot}%{_prefix}/Applications
silica-bundle build --info linux/Info.toml.in \
  --set VERSION="$version" --set BUILD=%{snapdate} --set DEVELOPER_KEY=unsigned \
  --flutter bundle --icon icon -o %{buildroot}%{_prefix}/Applications
# Its desktop entry, for the tools outside Silica (X-Silica-Bundle names the bundle).
silica-bundle desktop "%{buildroot}%{_prefix}/Applications/Terminal.app" --location system \
  | sed 's|%{buildroot}||g' > %{appid}.desktop
install -Dpm 0644 %{appid}.desktop %{buildroot}%{_datadir}/applications/%{appid}.desktop

%check
# OnlyShowIn=Silica is not a registered desktop name for desktop-file-validate (it wants
# X- values); the rest of the entry is validated.
sed '/^OnlyShowIn=/d' %{buildroot}%{_datadir}/applications/%{appid}.desktop > check.desktop
desktop-file-validate check.desktop

%files
%license LICENSE-MIT LICENSE-APACHE fonts/OFL.txt
%doc README.md
%{_prefix}/Applications/Terminal.app/
%{_datadir}/applications/%{appid}.desktop

%changelog
* Mon Oct 19 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261019git37e4047-1
- Terminal as an app bundle in /usr/Applications (silica-packages#7)

* Thu Oct 15 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261015git3dd25f3-1
- Update to the current main (release 0.1.2)

* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261014gitfb743ae-1
- First package
