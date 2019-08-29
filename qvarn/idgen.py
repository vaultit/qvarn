# idgen.py - generate resource identifiers
#
# Copyright 2015, 2016 Suomen Tilaajavastuu Oy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Implementation discussion
# =========================
#
# A resource identifier must be unique, efficient, secure, and
# private. These not in priority order: all requirements must be
# fulfilled. Additionally, it would be good for identifiers to be
# practical.
#
# Uniqueness and efficiency
# -------------------------
#
# Uniqueness can be provided by having a central database in which all
# identifiers exist, and adding new ones there. This is a performance
# bottleneck. We choose to rely on good, large random numbers instead.
# Quoting Wikipedia on random UUIDs:
#
#       To put these numbers into perspective, the annual risk of a
#       given person being hit by a meteorite is estimated to be one
#       chance in 17 billion,[4] which means the probability is about
#       0.00000000006 (6 * 10**11), equivalent to the odds of creating
#       a few tens of trillions of UUIDs in a year and having one
#       duplicate. In other words, only after generating 1 billion
#       UUIDs every second for the next 100 years, the probability of
#       creating just one duplicate would be about 50%.
#
# See http://en.wikipedia.org/wiki/Universally_unique_identifier.
#
# We do not used the UUID format specifically, but the principle
# holds. If get random numbers from a high-quality source, and use at
# least 128 bits of randomness (UUID4 uses 122), we're good. A bug in
# other parts of our software, the database software, the operating
# system, hardware, or operational procedures is more likely to cause
# duplicates.
#
# Security and privacy
# --------------------
#
# We want our identifiers to avoid leaking information. A linear
# counter, for example, would leak information: the number of resource
# objects created. We also can't use external identifiers, such as
# social security identifiers, as parts of resource identifiers, as
# this would leak actual sensitive information. Using random numbers
# is perfect.
#
# For added privacy, it would be good if different API clients would
# get different identifiers for the same resource. This would make it
# more difficult for them to combine data and endanger people's
# privacy. This level of protection is currently not handled at all,
# and in any case will probably not handled by this class. Instead, if
# we want to do this, we'll add a translation layer that changes
# internal identifiers to be per-client ones, and back again.
#
# Error checking
# --------------
#
# Inevitably, resource identifiers will show up in URLs, in log files,
# and be communicated by humans using writing or voice. To make these
# things easier, it would be good to be able to verify that an
# identifier looks correct, by adding error checking into the identifier.
#
# Further, it would be good to have type information: is this
# identifier one for a person or an organisation? This can catch
# attempts at using an identifier for the wrong type of resource.
#
# Identifier strucure
# -------------------
#
# Based on the above discussion, we define the following structure for
# a resource identifier:
#
#       * 16 bits of type field
#       * 128 bits of randomness
#       * 32 bits of error checking
#
# The type field is the top 16 bits of a SHA-512 of the resources type:
# effectively this:
#
#       hashlib.sha512(u'person').hexdigest()[:4]
#
# The random bits are read directly from /dev/urandom. Python provides
# os.urandom and uuid.uuid4, which could either be used, but to avoid
# having to trust Python's implementation, we read /dev/urandom
# directly.
#
# The error checking is done by computing the SHA-512 of the rest of
# the identifier and taking the top 32 bits:
#
#       hashlib.sha512(rest).hexdigest()[:8]
#
# For human convenience, we allow identifiers (which are effectively
# very large hexadecimal numbers) to be represented in upper or lower
# case, and that any non-hexdigits are ignored.
#
# The canonical form of an identifier (in this case, for a person):
#
#       0035-94c4f55599453307002f0731e0b67999-9ffa4cf4


import hashlib
import codecs


class ResourceIdGenerator(object):

    '''Generate resource identifiers.'''

    def __init__(self):
        self._urandom = URandom()

    def new_id(self, resource_type):
        '''Generate a new identifier.'''

        type_field = self._encode_type(resource_type)
        random_field = self._get_randomness()
        checksum_field = self._compute_checksum(type_field + random_field)
        return self._canonical_form(type_field, random_field, checksum_field)

    def _encode_type(self, resource_type):
        return hashlib.sha512(resource_type.encode('UTF-8')).hexdigest()[:4]

    def _get_randomness(self):
        num_bits = 128
        num_bytes = num_bits // 8
        random_bytes = self._urandom.get_random_bytes(num_bytes)
        return codecs.encode(random_bytes, 'hex').decode('ASCII')

    def _compute_checksum(self, rest):
        return hashlib.sha512(rest.encode('UTF-8')).hexdigest()[:8]

    def _canonical_form(self, type_field, random_field, checksum_field):
        return u'{0}-{1}-{2}'.format(type_field, random_field, checksum_field)


class URandom(object):

    def __init__(self):
        self._handle = None

    def get_random_bytes(self, num_bytes):
        f = self._open()
        return f.read(num_bytes)

    def _open(self):
        if self._handle is None:
            self._handle = open('/dev/urandom', 'rb')
        return self._handle
