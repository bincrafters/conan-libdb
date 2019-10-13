from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os
import shutil


class LibdbConan(ConanFile):
    name = "libdb"
    version = "6.2.32"
    description = "Berkeley DB is a family of embedded key-value database libraries providing scalable high-performance data management services to applications. The Berkeley DB products use simple function-call APIs for data access and management."
    topics = ("conan", "gdbm", "dbm", "hash", "database")
    url = "https://github.com/bincrafters/conan-libdb"
    homepage = "https://www.oracle.com/database/berkeley-db/"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = ("BSD", "LGPLv2", "Sleepycat")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tcl": [True, False],
        "historic": [True, False],
        "smallbuild": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "tcl": True,
        "historic": True,
        "smallbuild": True,
    }
    no_copy_sources = True
    _source_subfolder = "sources"

    @property
    def _mingw_build(self):
        return self.settings.compiler == "gcc" and self.settings.os == "Windows"

    def config_options(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        if self.options.shared:
            del self.options.fPIC

    def requirements(self):
        if self.options.tcl:
            self.requires("tcl/8.6.9@bincrafters/stable")

    def source(self):
        url = "http://download.oracle.com/berkeley-db/db-{version}.tar.gz".format(version=self.version)
        sha256 = "a9c5e2b004a5777aa03510cfe5cd766a4a3b777713406b02809c17c8e0e7a8fb"
        tools.get(url, sha256=sha256)
        os.rename("db-{}".format(self.version), self._source_subfolder)

        dist_configure = os.path.join(self.source_folder, self._source_subfolder, "dist", "configure")
        tools.replace_in_file(dist_configure, "../$sqlite_dir", "$sqlite_dir")
        tools.replace_in_file(dist_configure,
                              "\n    --disable-option-checking)",
                              "\n    --datarootdir=*)"
                              "\n      ;;"
                              "\n    --disable-option-checking)")

    def build(self):
        autotools = AutoToolsBuildEnvironment(self)
        conf_args = [
            "--enable-debug" if self.settings.build_type == "Debug" else "--disable-debug",
            "--disable-static" if self.options.shared else "--enable-static",
            "--enable-shared" if self.options.shared else "--disable-shared",
            "--disable-static" if self.options.shared else "--enable-static",
            "--enable-smallbuild" if self.options.smallbuild else "--disable-smallbuild",
            "--enable-dbm" if self.options.historic else "--disable-dbm",
            "--enable-mingw" if self._mingw_build else "--disable-mingw",
            "--enable-cxx",
            "--enable-compat185",
            "--enable-stl",
            # "--enable-dump185",
            "--enable-sql",
        ]
        if self.options.tcl:
            conf_args.append("--with-tcl={}".format(os.path.join(self.deps_cpp_info["tcl"].rootpath, "lib")))
        if not self.options.shared:
            conf_args.append("--with-pic" if self.options.fPIC else "--without-pic")
        with tools.chdir(self.build_folder):
            autotools.configure(configure_dir=os.path.join(self.source_folder, self._source_subfolder, "dist"), args=conf_args)
            autotools.make()

    def package(self):
        with tools.chdir(self.build_folder):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.install()
        shutil.rmtree(os.path.join(self.package_folder, "docs"))

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = ["db", "db_cxx", "db_stl", "db_sql"]
        if self.options.tcl:
            self.cpp_info.libs.append("db_tcl")
