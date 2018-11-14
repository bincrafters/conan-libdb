# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.util.env_reader import get_env
import os
import shutil
import tempfile


class LibdbConan(ConanFile):
    name = "libdb"
    version = "5.3.28"
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
    no_copy_source = True
    _source_subfolder = "sources"

    @property
    def _mingw_build(self):
        return self.settings.compiler == "gcc" and self.settings.os == "Windows"

    def config_options(self):
        if self.options.shared or self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    def requirements(self):
        if self.options.tcl:
            self.requires("tcl/8.6.9@bincrafters/stable")

    def source(self):
        filename = "db-{}.tar.gz".format(self.version)
        url = "http://download.oracle.com/berkeley-db/{}".format(filename)
        sha256 = "e0a992d740709892e81f9d93f06daf305cf73fb81b545afe72478043172c3628"

        dlfilepath = os.path.join(tempfile.gettempdir(), filename)
        if os.path.exists(dlfilepath) and not get_env("LIBDB_FORCE_DOWNLOAD", False):
            self.output.info("Skipping download. Using cached {}".format(dlfilepath))
        else:
            tools.download(url, dlfilepath)
        tools.check_sha256(dlfilepath, sha256)
        tools.untargz(dlfilepath)
        os.rename("{}-{}".format("db", self.version), self._source_subfolder)

        dist_configure = os.path.join(self.source_folder, self._source_subfolder, "dist", "configure")
        tools.replace_in_file(dist_configure, "../$sqlite_dir", "$sqlite_dir")
        tools.replace_in_file(dist_configure,
                              "\n    --disable-option-checking)",
                              "\n    --datarootdir=*)"
                              "\n      ;;"
                              "\n    --disable-option-checking)")

        tools.replace_in_file(os.path.join(self.source_folder, self._source_subfolder, "src", "dbinc", "atomic.h"),
                              "__atomic_compare_exchange",
                              "__db_atomic_compare_exchange")

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
        if self.should_build:
            with tools.chdir(self.build_folder):
                autotools.configure(configure_dir=os.path.join(self.source_folder, self._source_subfolder, "dist"), args=conf_args)
                autotools.make()

    def package(self):
        if self.should_install:
            with tools.chdir(self.build_folder):
                autotools = AutoToolsBuildEnvironment(self)
                autotools.install()
            shutil.rmtree(os.path.join(self.package_folder, "docs"))

    def package_info(self):
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libs = tools.collect_libs(self)
