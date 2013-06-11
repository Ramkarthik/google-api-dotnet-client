#!/usr/bin/python2.7
# Copyright 2010 Google Inc. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Tests for template_objects.py."""

__author__ = 'aiuto@google.com (Tony Aiuto)'


from django import template as django_template

from google.apputils import basetest

from googleapis.codegen import template_objects
from googleapis.codegen.language_model import LanguageModel


class TemplateObjectsTest(basetest.TestCase):

  def setUp(self):
    super(TemplateObjectsTest, self).setUp()
    self.language_model = LanguageModel(class_name_delimiter='|')

  def testFullyQualifiedClassName(self):
    foo = template_objects.CodeObject({'className': 'Foo'}, None,
                                      language_model=self.language_model)
    foo._module = template_objects.Module('test',
                                          language_model=self.language_model)
    bar = template_objects.CodeObject({'className': 'Bar'}, None, parent=foo)
    baz = template_objects.CodeObject({'className': 'Baz'}, None, parent=bar)

    self.assertEquals('test|Foo|Bar|Baz', baz.fullClassName)
    self.assertEquals('', baz.RelativeClassName(baz))
    self.assertEquals('Baz', baz.RelativeClassName(bar))
    self.assertEquals('Bar|Baz', baz.RelativeClassName(foo))

  def testModule(self):
    m = template_objects.Module('hello/world',
                                language_model=self.language_model)
    self.assertEquals('hello|world', m.name)
    self.assertEquals('hello/world', m.path)

  def testModuleParenting(self):
    m = template_objects.Module('hello/world',
                                language_model=self.language_model)
    child = template_objects.Module('everyone', parent=m)
    self.assertEquals('hello|world|everyone', child.name)
    self.assertEquals('hello/world/everyone', child.path)

  def testModuleNaming(self):
    p = template_objects.Module('hello/world',
                                language_model=self.language_model)
    foo = template_objects.CodeObject({'className': 'Foo'}, None,
                                      language_model=self.language_model)
    foo._module = p
    bar = template_objects.CodeObject({'className': 'Bar'}, None, parent=foo)
    baz = template_objects.CodeObject({'className': 'Baz'}, None, parent=bar)

    self.assertEquals('Foo|Bar|Baz', baz.packageRelativeClassName)
    self.assertEquals('hello|world|Foo|Bar|Baz', baz.fullClassName)

  def testParentPath(self):
    foo = template_objects.CodeObject({'className': 'Foo'}, None,
                                      language_model=self.language_model)
    bar = template_objects.CodeObject({'className': 'Bar'}, None, parent=foo)
    baz = template_objects.CodeObject({'className': 'Baz'}, None, parent=bar)
    self.assertEquals(['Foo', 'Bar'], baz.parentPath)

  def _TestRender(self, source, ctxt, expected):
    t = django_template.Template(source)
    rendered = t.render(django_template.Context(ctxt))
    self.assertEquals(expected, rendered)

  def testSimpleUseableInTemplates(self):
    d = dict(x=1, y=2, z=3)
    useable = template_objects.UseableInTemplates(d)
    t = '{{o.x}}|{{o.y}}|{{o.z}}'
    self._TestRender(t, {'o': useable}, '1|2|3')

  def testUseableInTemplatesWithAttributes(self):

    class SubUseable(template_objects.UseableInTemplates):

      def __init__(self, def_dict):
        super(SubUseable, self).__init__(def_dict)
        self.foo = 'spam'

      @property
      def bar(self):
        return 'eggs'

      def nougat(self):  # pylint:disable=g-bad-name
        return 'loukum'

      def codeName(self):  # pylint:disable=g-bad-name
        return 'ingot'

      def neverCalled(self):  # pylint:disable=g-bad-name
        raise Exception('This should never be called')

    d = dict(x=1, y=2, z=3, codeName='zorro')
    useable = SubUseable(d)
    t = ('{{o.x}}|{{o.y}}|{{o.z}}|{{o.foo}}|{{o.bar}}|{{o.nougat}}'
         '|{{o.codeName}}')
    self._TestRender(t, {'o': useable}, '1|2|3|spam|eggs|loukum|zorro')

    d = dict(neverCalled='here I am')
    useable = SubUseable(d)
    t = '{{o.neverCalled}}'
    self._TestRender(t, {'o': useable}, 'here I am')

if __name__ == '__main__':
  basetest.main()
