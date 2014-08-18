Name:           openblas
Version:        0.2.11
Release:        1%{?dist}
Summary:        An optimized BLAS library based on GotoBLAS2
Group:          Development/Libraries
License:        BSD
URL:            https://github.com/xianyi/OpenBLAS/
Source0:        https://github.com/xianyi/OpenBLAS/archive/v%{version}.tar.gz
# Use system lapack
Patch0:         openblas-0.2.11-system_lapack.patch
# Drop extra p from threaded library name
Patch1:         openblas-0.2.5-libname.patch
# Don't test link against functions in lapacke 3.5.0 if only 3.4.0 is available
Patch2:         openblas-0.2.10-lapacke.patch
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:  gcc-gfortran
# For execstack
BuildRequires:  prelink
# LAPACK
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
BuildRequires:  lapack-devel%{?_isa}
%else
BuildRequires:  lapack-static%{?_isa}
%endif

# Compability for old versions of GCC
%if 0%{?rhel} == 5
%global avxflag NO_AVX=1
%endif

# Do we have LAPACKE? (Needs at least lapack 3.4.0)
%if 0%{?fedora} > 16
%global lapacke 1
%else
%global lapacke 0
%endif

# Build 64-bit interface binaries?
%if 0%{?rhel} == 5 || 0%{?rhel} == 6
# RPM too old to know __isa_bits in RHEL 5, and lapack64 doesn't exist in RHEL 6
%global build64 0
%else
%if 0%{?__isa_bits} == 64
%global build64 1
%else
%global build64 0
%endif
%endif

%if %build64
BuildRequires:  lapack64-static
%endif

# Upstream supports the package only on these architectures.
# Runtime processor detection is not available on other archs.
ExclusiveArch:  x86_64 %{ix86}

%global base_description \
OpenBLAS is an optimized BLAS library based on GotoBLAS2 1.13 BSD \
version. The project is supported by the Lab of Parallel Software and \
Computational Science, ISCAS. http://www.rdcps.ac.cn


%description
%{base_description}

%package openmp
Summary:        An optimized BLAS library based on GotoBLAS2, OpenMP version
Group:          Development/Libraries

%description openmp
%{base_description}

This package contains the library compiled with OpenMP support.

%package threads
Summary:        An optimized BLAS library based on GotoBLAS2, pthreads version
Group:          Development/Libraries

%description threads
%{base_description}

This package contains the library compiled with threading support.

%if %build64
%package serial64
Summary:        An optimized BLAS library based on GotoBLAS2, serial version
Group:          Development/Libraries

%description serial64
%{base_description}

This package contains the sequential library compiled with a 64-bit
interface.

%package openmp64
Summary:        An optimized BLAS library based on GotoBLAS2, OpenMP version
Group:          Development/Libraries

%description openmp64
%{base_description}

This package contains the library compiled with OpenMP support and
64-bit interface.

%package threads64
Summary:        An optimized BLAS library based on GotoBLAS2, pthreads version
Group:          Development/Libraries

%description threads64
%{base_description}

This package contains the library compiled with threading support and
64-bit interface.
%endif


%package devel
Summary:        Development headers and libraries for OpenBLAS
Group:          Development/Libraries
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{name}-openmp%{?_isa} = %{version}-%{release}
Requires:       %{name}-threads%{?_isa} = %{version}-%{release}
%if %build64
Requires:       %{name}-openmp64%{?_isa} = %{version}-%{release}
Requires:       %{name}-threads64%{?_isa} = %{version}-%{release}
Requires:       %{name}-serial64%{?_isa} = %{version}-%{release}
%endif

%description devel
%{base_description}

This package contains the development headers and libraries.

%package static
Summary:        Static version of OpenBLAS
Group:          Development/Libraries
Requires:       %{name}-devel%{?_isa} = %{version}-%{release}

%description static
%{base_description}

This package contains the static libraries.

%prep
%setup -q -c -T

# Untar source
tar zxf %{SOURCE0}
cd OpenBLAS-%{version}
%patch0 -p1 -b .system_lapack
%patch1 -p1 -b .libname
%if 0%{?fedora} > 0 && 0%{?fedora} < 21
%patch2 -p1 -b .lapacke
%endif

# Get rid of bundled LAPACK sources
rm -rf lapack-netlib

# Make serial, threaded and OpenMP versions; as well as 64-bit versions
cd ..
cp -ar OpenBLAS-%{version} openmp
cp -ar OpenBLAS-%{version} threaded
%if %build64
cp -ar OpenBLAS-%{version} openmp64
cp -ar OpenBLAS-%{version} threaded64
cp -ar OpenBLAS-%{version} serial64
%endif
mv OpenBLAS-%{version} serial

# Setup 32-bit interface LAPACK
mkdir netliblapack
cd netliblapack
ar x %{_libdir}/liblapack_pic.a
# Get rid of duplicate functions. See list in Makefile of lapack directory
for f in laswp getf2 getrf potf2 potrf lauu2 lauum trti2 trtri getrs; do
    \rm {c,d,s,z}$f.o
done

# LAPACKE
%if %{lapacke}
ar x %{_libdir}/liblapacke.a
%endif

# Create makefile
echo "TOPDIR = .." > Makefile
echo "include ../Makefile.system" >> Makefile
echo "COMMONOBJS = \\" >> Makefile
for i in *.o; do
 echo "$i \\" >> Makefile
done
echo -e "\n\ninclude \$(TOPDIR)/Makefile.tail" >> Makefile

%if %{lapacke}
# Copy include files
cp -a %{_includedir}/lapacke .
%endif
cd ..

# Copy in place
for d in serial threaded openmp; do
    cp -pr netliblapack $d
done
rm -rf netliblapack


# Setup 64-bit interface LAPACK
%if %build64
mkdir netliblapack64
cd netliblapack64
ar x %{_libdir}/liblapack64_pic.a
# Get rid of duplicate functions. See list in Makefile of lapack directory
for f in laswp getf2 getrf potf2 potrf lauu2 lauum trti2 trtri getrs; do
    \rm {c,d,s,z}$f.o
done

# LAPACKE, no 64-bit interface
%if %{lapacke}
ar x %{_libdir}/liblapacke.a
%endif

# Create makefile
echo "TOPDIR = .." > Makefile
echo "include ../Makefile.system" >> Makefile
echo "COMMONOBJS = \\" >> Makefile
for i in *.o; do
    echo "$i \\" >> Makefile
done
echo -e "\n\ninclude \$(TOPDIR)/Makefile.tail" >> Makefile

%if %{lapacke}
# Copy include files
cp -a %{_includedir}/lapacke .
%endif
cd ..

# Copy in place
for d in serial64 threaded64 openmp64; do
    cp -pr netliblapack64 $d/netliblapack
done
rm -rf netliblapack64
%endif

%build
%if %{lapacke}
LAPACKE="NO_LAPACKE=0"
%else
LAPACKE="NO_LAPACKE=1"
%endif

# Maximum possible amount of processors
NMAX="NUM_THREADS=128"

make -C serial     TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=0 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" $NMAX LIBPREFIX="libopenblas"    %{?avxflag} $LAPACKE INTERFACE64=0
make -C threaded   TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=1 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" $NMAX LIBPREFIX="libopenblasp"   %{?avxflag} $LAPACKE INTERFACE64=0
# USE_THREAD determines use of SMP, not of pthreads
make -C openmp     TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=1 USE_OPENMP=1 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" $NMAX LIBPREFIX="libopenblaso"   %{?avxflag} $LAPACKE INTERFACE64=0

%if %build64
make -C serial64   TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=0 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" $NMAX LIBPREFIX="libopenblas64"  %{?avxflag} $LAPACKE INTERFACE64=1
make -C threaded64 TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=1 USE_OPENMP=0 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" $NMAX LIBPREFIX="libopenblasp64" %{?avxflag} $LAPACKE INTERFACE64=1
make -C openmp64   TARGET=CORE2 DYNAMIC_ARCH=1 USE_THREAD=1 USE_OPENMP=1 FC=gfortran CC=gcc COMMON_OPT="%{optflags}" $NMAX LIBPREFIX="libopenblaso64" %{?avxflag} $LAPACKE INTERFACE64=1
%endif

%install
rm -rf %{buildroot}
# Install serial library and headers
make -C serial USE_THREAD=0 PREFIX=%{buildroot}%{_usr} install

# Move include files to package specific directory, so that they don't clash with reference BLAS and LAPACK
mkdir %{buildroot}%{_includedir}/%{name}
mv %{buildroot}%{_includedir}/*.h %{buildroot}%{_includedir}/%{name}

# Copy lapacke include files
%if %{lapacke}
cp -a %{_includedir}/lapacke %{buildroot}%{_includedir}/%{name}
%endif

# Put libraries in correct location
if [ %_lib != lib ]; then
 mkdir -p %{buildroot}%{_libdir}
 mv %{buildroot}/usr/lib/libopen* %{buildroot}%{_libdir}
fi

# Fix name of static library
slibname=`basename %{buildroot}%{_libdir}/libopenblas-*.so .so`
mv %{buildroot}%{_libdir}/${slibname}.a %{buildroot}%{_libdir}/lib%{name}.a

# Install the OpenMP library
olibname=`echo ${slibname} | sed "s|lib%{name}|lib%{name}o|g"`
install -D -p -m 755 openmp/${olibname}.so %{buildroot}%{_libdir}/${olibname}.so
install -D -p -m 644 openmp/${olibname}.a %{buildroot}%{_libdir}/lib%{name}o.a

# Install the threaded library
plibname=`echo ${slibname} | sed "s|lib%{name}|lib%{name}p|g"`
install -D -p -m 755 threaded/${plibname}.so %{buildroot}%{_libdir}/${plibname}.so
install -D -p -m 644 threaded/${plibname}.a %{buildroot}%{_libdir}/lib%{name}p.a

# Install the 64-bit interface libraries
%if %build64
slibname64=`echo ${slibname} | sed "s|lib%{name}|lib%{name}64|g"`
install -D -p -m 755 serial64/${slibname64}.so %{buildroot}%{_libdir}/${slibname64}.so
install -D -p -m 644 serial64/${slibname64}.a %{buildroot}%{_libdir}/lib%{name}64.a

olibname64=`echo ${slibname} | sed "s|lib%{name}|lib%{name}o64|g"`
install -D -p -m 755 openmp64/${olibname64}.so %{buildroot}%{_libdir}/${olibname64}.so
install -D -p -m 644 openmp64/${olibname64}.a %{buildroot}%{_libdir}/lib%{name}o64.a

plibname64=`echo ${slibname} | sed "s|lib%{name}|lib%{name}p64|g"`
install -D -p -m 755 threaded64/${plibname64}.so %{buildroot}%{_libdir}/${plibname64}.so
install -D -p -m 644 threaded64/${plibname64}.a %{buildroot}%{_libdir}/lib%{name}p64.a
%endif

# Fix source permissions (also applies to LAPACK)
find -name \*.f -exec chmod 644 {} \;

# Fix symlinks
pushd %{buildroot}%{_libdir}
# Serial libraries
ln -sf ${slibname}.so lib%{name}.so
ln -sf ${slibname}.so lib%{name}.so.0
# OpenMP libraries
ln -sf ${olibname}.so lib%{name}o.so
ln -sf ${olibname}.so lib%{name}o.so.0
# Threaded libraries
ln -sf ${plibname}.so lib%{name}p.so
ln -sf ${plibname}.so lib%{name}p.so.0

%if %build64
# Serial libraries
ln -sf ${slibname64}.so lib%{name}64.so
ln -sf ${slibname64}.so lib%{name}64.so.0
# OpenMP libraries
ln -sf ${olibname64}.so lib%{name}o64.so
ln -sf ${olibname64}.so lib%{name}o64.so.0
# Threaded libraries
ln -sf ${plibname64}.so lib%{name}p64.so
ln -sf ${plibname64}.so lib%{name}p64.so.0
%endif


# Get rid of executable stacks
for lib in %{buildroot}%{_libdir}/libopenblas{,o,p}-*.so; do
 execstack -c $lib
done

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%post openmp -p /sbin/ldconfig
%postun openmp -p /sbin/ldconfig

%post threads -p /sbin/ldconfig
%postun threads -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%doc serial/Changelog.txt serial/GotoBLAS* serial/LICENSE
%{_libdir}/lib%{name}-*.so
%{_libdir}/lib%{name}.so.*

%files openmp
%defattr(-,root,root,-)
%{_libdir}/lib%{name}o-*.so
%{_libdir}/lib%{name}o.so.*

%files threads
%defattr(-,root,root,-)
%{_libdir}/lib%{name}p-*.so
%{_libdir}/lib%{name}p.so.*

%if %build64
%files serial64
%defattr(-,root,root,-)
%{_libdir}/lib%{name}64-*.so
%{_libdir}/lib%{name}64.so.*

%files openmp64
%defattr(-,root,root,-)
%{_libdir}/lib%{name}o64-*.so
%{_libdir}/lib%{name}o64.so.*

%files threads64
%defattr(-,root,root,-)
%{_libdir}/lib%{name}p64-*.so
%{_libdir}/lib%{name}p64.so.*
%endif

%files devel
%defattr(-,root,root,-)
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{name}o.so
%{_libdir}/lib%{name}p.so
%if %build64
%{_libdir}/lib%{name}64.so
%{_libdir}/lib%{name}o64.so
%{_libdir}/lib%{name}p64.so
%endif

%files static
%defattr(-,root,root,-)
%{_libdir}/lib%{name}.a
%{_libdir}/lib%{name}o.a
%{_libdir}/lib%{name}p.a
%if %build64
%{_libdir}/lib%{name}64.a
%{_libdir}/lib%{name}o64.a
%{_libdir}/lib%{name}p64.a
%endif

%changelog
* Mon Aug 18 2014 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.11-1
- Update to 0.2.11.

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Jul 16 2014 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.10-1
- Update to 0.2.10.

* Wed Jun 11 2014 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.9-1
- Increase maximum amount of cores from 32 to 128.
- Add 64-bit interface support. (BZ #1088256)
- Update to 0.2.9. (BZ #1043083)

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Aug 07 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.8-1
- Update to 0.2.8.

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 23 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.7-1
- Update to 0.2.7.
- Use OpenBLAS versions of LAPACK functions, as they seem to be
  working now.

* Mon Jul 08 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-10
- Due to long standing bug, replace all OpenBLAS LAPACK functions with
  generic ones, so that package can finally be released in stable.

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.5-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 15 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-8
- Added LAPACKE include files.

* Mon Jan 14 2013 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-7
- Fix build on RHEL5 and ppc architecture.

* Mon Dec 24 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-6
- Review fixes.

* Fri Dec 21 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-5
- Disable LAPACKE support on distributions where it is not available due to
  a too old version of lapack.

* Mon Dec 17 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-4
- Don't use reference LAPACK functions that have optimized implementation.

* Wed Dec 12 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-3
- Use system version of LAPACK.

* Mon Nov 26 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-2
- Fixed 32-bit build, and build on EPEL 5.

* Mon Nov 26 2012 Susi Lehtola <jussilehtola@fedoraproject.org> - 0.2.5-1
- Update to 0.2.5.

* Thu Oct 06 2011 Jussi Lehtola <jussilehtola@fedoraproject.org> - 0.1-2.alpha2.4
- Added documentation.

* Sun Sep 18 2011 Jussi Lehtola <jussilehtola@fedoraproject.org> - 0.1-1.alpha2.4
- First release.
