# __init__.py - manage package namespace for Qvarn
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


from .version import (
    __version__,
    __version_info__,
)

from .slog import (
    StructuredLog,
    NullSlogWriter,
    FileSlogWriter,
    SyslogSlogWriter,
    hijack_logging,
)

from .exc import (
    QvarnException,
)

from .http_statuses import (
    HTTPError,
    BadRequest,
    Unauthorized,
    Forbidden,
    NotFound,
    Conflict,
    LengthRequired,
    UnsupportedMediaType,
)

from .counter import (
    Counter,
)

from .walker import (
    ItemWalker,
    TooDeeplyNestedPrototype,
)

from .validate import (
    ItemValidator,
    ValidationError,
)

from .basic_validation_plugin import (
    BasicValidationPlugin,
    NoItemRevision,
    ContentTypeIsNotJSON,
)

from .sql import (
    SqliteAdapter,
    PostgresAdapter,
    column_types,
)

from .measurement import (
    Measurement,
)

from .transaction import (
    Transaction,
)

from .dbconn import (
    DatabaseConnection,
)

from .subitem_protos import (
    SubItemPrototypes,
)

from .write_only import (
    WriteOnlyStorage,
    CannotAddWithId,
    CannotAddWithRevision,
    WrongRevision,
)

from .read_only import (
    ReadOnlyStorage,
    ItemDoesNotExist,
    FieldNotInResource,
)

from .restype_storage import (
    ResourceTypeStorage,
)

from .backend_app import (
    BackendApplication,
    log,
)

from .filler import (
    add_missing_item_fields,
)

from .util import (
    route_to_scope,
    table_name,
    ComplicatedTableNameError,
    create_tables_for_resource_type,
)

from .simple_resource import (
    SimpleResource,
)

from .list_resource import (
    ListResource,
)

from .idgen import (
    ResourceIdGenerator,
)

from .authorization_plugin import (
    AuthorizationPlugin,
)

from .authorization_validator import (
    AuthorizationValidator,
)

from .logging_plugin import (
    LoggingPlugin,
)

from .string_to_unicode_plugin import (
    StringToUnicodePlugin,
)

from .listener_resource import (
    ListenerResource,
    listener_prototype,
    notification_prototype,
)

from .file_resource import (
    FileResource,
    ContentLengthMissing,
    InvalidContentType,
)

from .error_transform_plugin import (
    ErrorTransformPlugin,
)

from .schema import (
    schema_from_prototype,
)

from .versioned_storage import (
    VersionedStorage,
)

from .resource_server import (
    ResourceServer,
    add_resource_type_to_server,
)
