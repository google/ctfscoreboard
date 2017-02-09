# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from scoreboard import utils


def test_normalize_input():
    # Sanity checking
    assert utils.normalize_input("hello") == "hello"
    assert not utils.normalize_input("hello") == "world"

    # Test normalize_input on preceding whitespace
    assert utils.normalize_input(" hello") == "hello"
    assert utils.normalize_input("    hello") == "hello"
    assert utils.normalize_input("\thello") == "hello"
    assert utils.normalize_input(" \n hello") == "hello"
    assert utils.normalize_input("\t\nhello") == "hello"

    # Test normalize_input on trailing whitespace
    assert utils.normalize_input("hello ") == "hello"
    assert utils.normalize_input("hello    ") == "hello"
    assert utils.normalize_input("hello\t") == "hello"
    assert utils.normalize_input("hello \n ") == "hello"
    assert utils.normalize_input("hello\n\t") == "hello"

    # Test normalize_input on encompassing whitespace
    assert utils.normalize_input(" hello ") == "hello"
    assert utils.normalize_input(" hello\n ") == "hello"
    assert utils.normalize_input(" \nhello ") == "hello"
    assert utils.normalize_input("\t\thello\n\n") == "hello"
    assert utils.normalize_input(" \t\nhello\n\t ") == "hello"

    # Test normalize_input on encompassed whitespace
    assert utils.normalize_input("hello world") == "hello world"
    assert utils.normalize_input("  hello world") == "hello world"
    assert utils.normalize_input("hello world  ") == "hello world"
    assert utils.normalize_input("  hello world  ") == "hello world"
    assert utils.normalize_input("\t\n hello world \n\t") == "hello world"

    # Test normalize_input on uppercase text
    assert utils.normalize_input("Hello") == "hello"
    assert utils.normalize_input("HELLO") == "hello"
    assert utils.normalize_input("hElLo") == "hello"
    assert utils.normalize_input("HeLlO") == "hello"
    assert utils.normalize_input(" \t\n  HeLlO \t\n ") == "hello"

    # Test normalize_input on common flag formats
    assert utils.normalize_input("CTF{ }") == \
        "ctf{ }"

    assert utils.normalize_input("this_is_a_flag") == \
        "this_is_a_flag"
    assert utils.normalize_input("CTF{this_is_a_flag}") == \
        "ctf{this_is_a_flag}"
    assert utils.normalize_input("\t CTF{this_is_a_flag} \n") == \
        "ctf{this_is_a_flag}"
    assert utils.normalize_input("\t CTF{THIS_IS_A_FLAG} \n") == \
        "ctf{this_is_a_flag}"

    assert utils.normalize_input("this-is-a-flag") == \
        "this-is-a-flag"
    assert utils.normalize_input("CTF{this-is-a-flag}") == \
        "ctf{this-is-a-flag}"
    assert utils.normalize_input("\t CTF{this-is-a-flag} \n") == \
        "ctf{this-is-a-flag}"
    assert utils.normalize_input("\t CTF{THIS-IS-A-FLAG} \n") == \
        "ctf{this-is-a-flag}"

    assert utils.normalize_input("this,is,a,flag") == \
        "this,is,a,flag"
    assert utils.normalize_input("CTF{this,is,a,flag}") == \
        "ctf{this,is,a,flag}"
    assert utils.normalize_input("\t CTF{this,is,a,flag} \n") == \
        "ctf{this,is,a,flag}"
    assert utils.normalize_input("\t CTF{THIS,IS,A,FLAG} \n") == \
        "ctf{this,is,a,flag}"

    assert utils.normalize_input("this/is/a/flag") == \
        "this/is/a/flag"
    assert utils.normalize_input("CTF{this/is/a/flag}") == \
        "ctf{this/is/a/flag}"
    assert utils.normalize_input("\t CTF{this/is/a/flag} \n") == \
        "ctf{this/is/a/flag}"
    assert utils.normalize_input("\t CTF{THIS/IS/A/FLAG} \n") == \
        "ctf{this/is/a/flag}"

    assert utils.normalize_input("this|is|a|flag") == \
        "this|is|a|flag"
    assert utils.normalize_input("CTF{this|is|a|flag}") == \
        "ctf{this|is|a|flag}"
    assert utils.normalize_input("\t CTF{this|is|a|flag} \n") == \
        "ctf{this|is|a|flag}"
    assert utils.normalize_input("\t CTF{THIS|IS|A|FLAG} \n") == \
        "ctf{this|is|a|flag}"

    assert utils.normalize_input("this+is+a+flag") == \
        "this+is+a+flag"
    assert utils.normalize_input("CTF{this+is+a+flag}") == \
        "ctf{this+is+a+flag}"
    assert utils.normalize_input("\t CTF{this+is+a+flag} \n") == \
        "ctf{this+is+a+flag}"
    assert utils.normalize_input("\t CTF{THIS+IS+A+FLAG} \n") == \
        "ctf{this+is+a+flag}"

    return True


def test_all():
    test_normalize_input()

    return True


if __name__ == "__main__":
    test_all()
