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


# This shell script snippet gets prepended to each IMPLEMENTS step
# when it is executed. It can contain shared definitions of shell
# functions and similar stuff.


save_value()
{
    printf 's \$%s$ %s g\n' "$1" "$2" >> "$DATADIR/expand-values.sed"
    printf 's \$%s([^0-9]) %s\\1 g\n' "$1" "$2" >> "$DATADIR/expand-values.sed"
}


expand_values()
{
    touch "$DATADIR/expand-values.sed"
    echo "$1" | sed -r -f "$DATADIR/expand-values.sed"
}
