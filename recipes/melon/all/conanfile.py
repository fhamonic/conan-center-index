import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.0"


class MelonConan(ConanFile):
    name = "melon"
    description = "Modern and Efficient Library for Optimization in Networks."
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/fhamonic/melon"
    topics = ("graph", "header-only", "cpp23", "algorithms")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return 23

    @property
    def _compilers_minimum_version(self):
        # The real constraint is the standard library, not the compiler (see
        # upstream's include/melon/detail/stdlib_check.hpp): gcc 14 is the
        # first release shipping libstdc++ 14, apple-clang 21 (Xcode 26.4)
        # the first shipping libc++ 20; clang 18 (paired with libstdc++ >= 14)
        # and msvc 194 are the oldest versions upstream CI tests.
        return {
            "gcc": "14",
            "clang": "18",
            "apple-clang": "21",
            "msvc": "194",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(
            self,
            "*.hpp",
            os.path.join(self.source_folder, "include"),
            os.path.join(self.package_folder, "include"),
            # melon/experimental/ ships, but two headers are still unfinished
            excludes=(
                "melon/experimental/scapegoat_tree.hpp",
                "melon/experimental/doubly_connected_digraph.hpp",
            ),
        )

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "melon")
        self.cpp_info.set_property("cmake_target_name", "melon::melon")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        # the knapsack_bnb headers use std::jthread and std::async
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
