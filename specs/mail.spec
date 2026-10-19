# prepare: rust engine
# prepare: flutter app

%global srcrepo mail
%global commit 2dd8b17b9714a1d5659f8e5e99fa1faa7de9b453
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapdate 20261019
%global appid dev.frascella.Mail

# The Dart AOT library is private (dlopen'ed by the embedder).
%global __provides_exclude_from ^%{_prefix}/Applications/.*$

Name:           mail
Version:        0^%{snapdate}git%{shortcommit}
Release:        1%{?dist}
Summary:        Mail, the email client of Silica

# Mail: MIT OR Apache-2.0. The engine's bundled Rust crates are listed in cargo-vendor.txt
# (licences in LICENSE.dependencies); the Dart packages of the app in
# flutter_assets/NOTICES.Z.
License:        (MIT OR Apache-2.0) AND LicenseRef-Bundled-Crates AND LicenseRef-Bundled-Dart
URL:            https://github.com/silica-os/mail
Source0:        %{srcrepo}-%{commit}.tar.gz
Source1:        %{srcrepo}-%{commit}-vendor-engine.tar.zst
Source2:        %{srcrepo}-%{commit}-dart-app.tar.zst
Source3:        dev.frascella.Mail.service

ExclusiveArch:  x86_64
BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  gcc
BuildRequires:  zstd
BuildRequires:  desktop-file-utils
# silica-bundle puts the app bundle together (silica-os docs/app-bundles.md).
BuildRequires:  silica-apps

Requires:       silica-embedder%{?_isa}
Requires:       silica-apps
Requires:       silica-mail-engine%{?_isa} = %{version}-%{release}
Recommends:     silica-icons

%description
Mail is Silica's email client: mailboxes, threads, search and the composer, on top of
silica-mail-engine.

%package -n silica-mail-engine
Summary:        IMAP and SMTP engine of Silica's Mail, on D-Bus

%description -n silica-mail-engine
silica-mail-engine syncs IMAP accounts, sends through SMTP and keeps an offline store; it
serves dev.frascella.Mail on the session bus (started on demand by D-Bus activation).

%prep
%autosetup -n %{srcrepo}-%{commit}
cd engine
zstd -dc %{SOURCE1} | tar -x
%cargo_prep -v vendor
cd ..
mkdir bundle
zstd -dc %{SOURCE2} | tar -x -C bundle

%build
cd engine
%cargo_build
%{cargo_license_summary -a}
%{cargo_license -a} > LICENSE.dependencies
%cargo_vendor_manifest

%install
install -Dpm 0755 engine/target/rpm/silica-mail-engine \
  %{buildroot}%{_libexecdir}/silica/silica-mail-engine
sed 's|@LIBEXECDIR@|%{_libexecdir}|' %{SOURCE3} > dev.frascella.Mail.service
install -Dpm 0644 dev.frascella.Mail.service \
  %{buildroot}%{_datadir}/dbus-1/services/dev.frascella.Mail.service

# Mail as an app bundle in /usr/Applications (silica-os#3, silica-os docs/app-bundles.md): a
# system app, allowed by its folder and run without a sandbox. Signing with the release key
# happens where the key is available (silica-bundle build --key); without it the bundle is
# unsigned.
version=$(sed -n 's/^version: *\([^+ ]*\).*/\1/p' app/pubspec.yaml)
install -dm 0755 %{buildroot}%{_prefix}/Applications
silica-bundle build --info app/linux/Info.toml.in \
  --set VERSION="$version" --set BUILD=%{snapdate} --set DEVELOPER_KEY=unsigned \
  --flutter bundle --icon app/icon -o %{buildroot}%{_prefix}/Applications
# Its desktop entry, for the tools outside Silica (X-Silica-Bundle names the bundle).
silica-bundle desktop "%{buildroot}%{_prefix}/Applications/Mail.app" --location system \
  | sed 's|%{buildroot}||g' > %{appid}.desktop
install -Dpm 0644 %{appid}.desktop %{buildroot}%{_datadir}/applications/%{appid}.desktop

%check
# OnlyShowIn=Silica is not a registered desktop name for desktop-file-validate (it wants
# X- values); the rest of the entry is validated.
sed '/^OnlyShowIn=/d' %{buildroot}%{_datadir}/applications/%{appid}.desktop > check.desktop
desktop-file-validate check.desktop

%files
%license LICENSE-MIT LICENSE-APACHE
%doc README.md
%{_prefix}/Applications/Mail.app/
%{_datadir}/applications/%{appid}.desktop

%files -n silica-mail-engine
%license LICENSE-MIT LICENSE-APACHE engine/LICENSE.dependencies engine/cargo-vendor.txt
%dir %{_libexecdir}/silica
%{_libexecdir}/silica/silica-mail-engine
%{_datadir}/dbus-1/services/dev.frascella.Mail.service

%changelog
* Mon Oct 19 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261019git2dd8b17-1
- Mail as an app bundle in /usr/Applications (silica-packages#7)

* Thu Oct 15 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261015git46285b2-1
- Update to the current main (release 0.1.2)

* Wed Oct 14 2026 Emanuele Frascella <emanuele@frascella.dev> - 0^20261014gita4e71f1-1
- First package
