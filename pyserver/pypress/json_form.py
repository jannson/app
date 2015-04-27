# coding: utf-8
import json
import jsonschema
from jsonschema.validators import Draft4Validator


class BaseField(object):

    default_template = """
    <div class="form-group">
        <div class="clearfix">
            <label class="desc" title="{name}" for="{input_id}">{name}<span class="req">*</span> </label>
            <div class="input">
                <input type="{input_type}" class="form-control {extra_classes}"
                name="{input_name}" value="" id="{input_id}">
            </div>
        </div>
    </div>
    """

    def __init__(
            self, name, input_type, input_name,
            input_id=None, extra_classes=None):
        self.name = name
        self.input_type = input_type
        self.input_name = input_name
        self.input_id = input_id
        if extra_classes is None:
            self.extra_classes = []
        else:
            self.extra_classes = extra_classes

    def render(self):
        return self.default_template.format(
            name=self.name,
            input_type=self.input_type,
            input_name=self.input_name,
            input_id=self.input_id,
            extra_classes=" ".join(self.extra_classes),
        )

    def __str__(self):
        return self.render()


class StringField(BaseField):

    def __init__(self, name, input_name, input_id=None, extra_classes=None):
        super(StringField, self).__init__(name, "text", input_name, input_id, extra_classes)


class IntegerField(BaseField):

    def __init__(self, name, input_name, input_id=None, extra_classes=None):
        super(IntegerField, self).__init__(name, "text", input_name, input_id, extra_classes)


class JsonForm(object):

    schema = {}
    generators = {
        "string": StringField,
        "number": IntegerField,
        }

    def __init__(self, json_data, live_schema=None):
        if not hasattr(json_data, '__getitem__'):
            raise TypeError('json_data must be a dict.')
        if not self.schema:
                raise NotImplementedError('schema not implemented!')
        if live_schema is not None:
            self.live_schema = live_schema
            self.schema['properties'].update(live_schema['properties'])
            if "required" in self.schema and "required" in live_schema:
                self.schema['required'] = list(set(self.schema['required']) | set(live_schema["required"]))

        Draft4Validator.check_schema(self.schema)

        self.data = {}
        self._filter_data(json_data, self.schema['properties'], self.data)
        self.validator = Draft4Validator(self.schema)
        self.errors = None

    def validate(self):
        try:
            self.validator.validate(self.data, self.schema)
            return True
        except jsonschema.ValidationError as e:
            self.errors = str(e)
            return False

    def _filter_data(self, data, properties, output):
        for key in data:
            if key in properties:
                if properties[key]['type'].lower() == 'object':
                    output[key] = {}
                    self._filter_data(data[key], properties[key]['properties'], output[key])
                elif properties[key]['type'].lower() == 'number':
                    try:
                        output[key] = int(data[key])
                    except (ValueError, TypeError):
                        output[key] = data[key]
                elif properties[key]['type'].lower() == 'string':
                    try:
                        output[key] = str(data[key])
                    except UnicodeEncodeError:
                        output[key] = data[key]
                else:
                    output[key] = data[key]

    @property
    def dumped_schema(self):
        return json.dumps(self.schema)

    @staticmethod
    def loads(input_string):
        return json.loads(input_string)

    @property
    def fields(self):
        fields = []
        propertries = self.schema['properties']
        for key, value in propertries.items():
            fields.append(
                self.generators[value["type"]](
                    name=value["name"],
                    input_name=key,
                    input_id=value["input_id"],
                    extra_classes=value['extra_classes']
                )
            )
        return fields

_schema = {
    "type": "object",
    "properties": {
        "to_uid": {
            "type": "number",
            "name": "测试样例",
            "input_id": "to_uid",
            "extra_classes": ["example_class", ],
            "pattern": "\d+",  # 正则表达式
        },
    },
    "required": ['to_uid', ],
}


# validation : http://json-schema.org/example2.html
# 使用额外的字段

def test():
    class Form(JsonForm):
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }

    form_data = {"to_uid": "fuck"}

    form = Form(json_data={}, live_schema=_schema)
    for field in form.fields:
        print field.render()
    form = Form(json_data=form_data, live_schema=_schema)
    if not form.validate():
        print form.errors


# 将所有validation放到form里

def test2():
    class Form(JsonForm):
        schema = {
            "type": "object",
            "properties": {
                "test_field": {
                    "type": "string",    # json_schema 所定义的字段类型
                    "name": "测试字段2",  # 渲染需要的字段名字
                    "input_id": "test_field",  # input的ID
                    "extra_classes": ["example_class", ],  # input的额外类
                    "pattern": "\d+",  # validation正则表达式
                },
            },
            "required": ['test_field', ],  # 必要字段
        }

    form_data = {"to_uid": "fuck", "test_field": "haha"}

    form = Form(json_data={}, live_schema=_schema)
    for field in form.fields:
        print field.render()

    form = Form(json_data=form_data, live_schema=_schema)
    if not form.validate():
        print form.errors

    # 序列化
    dumped_data = form.dumped_schema

    # 反序列化
    new_schema = JsonForm.loads(dumped_data)

    # 重新初始化
    form = Form(json_data=form_data, live_schema=new_schema)


if __name__ == "__main__":
    test()
    test2()