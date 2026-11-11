Name:		asciidoctorj-api
Version:	3.0.1
Release:	1
Summary:	Java API for AsciidoctorJ used by Gradle's documentation build
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/asciidoctor/asciidoctorj
# Tag v3.0.1 module asciidoctorj-api, Java sources and LICENSE.txt only.
# The implementation jar needs JRuby and is not part of this package.
Source0:	asciidoctorj-api-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem

%description
AsciidoctorJ API 3.0.1. Gradle 9.9.1's build catalog names
org.asciidoctor:asciidoctorj-api at this version. These are the Java
types the implementation is programmed against. package-info.java only
imports the OSGi Export annotation, which is not in cooker, and the
published API jar does not import org.osgi at runtime, so those six
files are left out of the compile.

%prep
%autosetup -n asciidoctorj-api-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print -delete
if find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) | grep -q .; then
	echo 'prebuilt binaries remain' >&2
	exit 1
fi

%build
set -eo pipefail
find org -name '*.java' ! -name 'package-info.java' > java.list
test "$(wc -l < java.list)" -eq 73
test "$(find org -name 'package-info.java' | wc -l)" -eq 6
mkdir -p classes
javac --release 11 -encoding UTF-8 -Xlint:-options -d classes @java.list
cat > manifest.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: org.asciidoctor.asciidoctorj.api

EOF
jar cfm asciidoctorj-api.jar manifest.mf -C classes .
jar i asciidoctorj-api.jar
javap -verbose -cp asciidoctorj-api.jar org.asciidoctor.SafeMode | grep -F 'major version: 55'
jar --describe-module -f asciidoctorj-api.jar > describe.txt
grep -F -q 'org.asciidoctor.asciidoctorj.api' describe.txt
if grep -F -q 'Unable' describe.txt; then
	cat describe.txt
	exit 1
fi

cat > asciidoctorj-api.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.asciidoctor</groupId>
  <artifactId>asciidoctorj-api</artifactId>
  <version>%{version}</version>
  <name>asciidoctorj-api</name>
  <description>API for AsciidoctorJ</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact asciidoctorj-api.pom:asciidoctorj-api.jar \
	--file-name asciidoctorj-api \
	--filelist .mfiles

%check
set -eo pipefail
mkdir -p check
cat > check/Smoke.java << 'EOF'
import org.asciidoctor.Options;
import org.asciidoctor.SafeMode;
import java.util.Map;

public class Smoke {
	public static void main(String[] args) {
		SafeMode mode = SafeMode.safeMode(20);
		if (mode != SafeMode.SECURE || mode.getLevel() != 20) {
			throw new RuntimeException("mode " + mode);
		}
		Options options = Options.builder().safe(mode).backend("html5").build();
		Map<String, Object> map = options.map();
		if (!Integer.valueOf(20).equals(map.get(Options.SAFE)) || !"html5".equals(map.get(Options.BACKEND))) {
			throw new RuntimeException(String.valueOf(map));
		}
		System.out.println("asciidoctor_api_ok SECURE html5 3.0.1");
	}
}
EOF
JAR=%{buildroot}%{_javadir}/asciidoctorj-api.jar
test -f "$JAR"
javac --release 11 -encoding UTF-8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'asciidoctor_api_ok SECURE html5 3.0.1' check/out.txt

%files -f .mfiles
%license LICENSE.txt
