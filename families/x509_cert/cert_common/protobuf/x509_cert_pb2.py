# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: cert_common/protobuf/x509_cert.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='cert_common/protobuf/x509_cert.proto',
  package='',
  syntax='proto3',
  serialized_options=_b('\n\030sawtooth.config.protobufP\001'),
  serialized_pb=_b('\n$cert_common/protobuf/x509_cert.proto\"0\n\x0cX509CertInfo\x12\x11\n\towner_key\x18\x01 \x01(\t\x12\r\n\x05xcert\x18\x02 \x01(\x0c\x42\x1c\n\x18sawtooth.config.protobufP\x01\x62\x06proto3')
)




_X509CERTINFO = _descriptor.Descriptor(
  name='X509CertInfo',
  full_name='X509CertInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='owner_key', full_name='X509CertInfo.owner_key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='xcert', full_name='X509CertInfo.xcert', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=40,
  serialized_end=88,
)

DESCRIPTOR.message_types_by_name['X509CertInfo'] = _X509CERTINFO
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

X509CertInfo = _reflection.GeneratedProtocolMessageType('X509CertInfo', (_message.Message,), dict(
  DESCRIPTOR = _X509CERTINFO,
  __module__ = 'cert_common.protobuf.x509_cert_pb2'
  # @@protoc_insertion_point(class_scope:X509CertInfo)
  ))
_sym_db.RegisterMessage(X509CertInfo)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)