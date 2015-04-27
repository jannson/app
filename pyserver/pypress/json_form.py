# coding: utf-8
import jsonschema
from jsonschema.validators import Draft4Validator


class BaseField(object):

    default_template = """
    <div class="form-group">
        <div class="clearfix">
            <label class="desc" title="{name}" for="{input_id}">{name}<span class="req">*</span> </label>
            <div class="input">
                <input type="{input_type}" class="form-control {extra_classes}"
                name="{input_name}" value="0" id="{input_id}">
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
        if live_schema is not None:
            self._schema = live_schema
        else:
            if not self.schema:
                raise NotImplementedError('schema not implemented!')
            self._schema = self.schema
        Draft4Validator.check_schema(self._schema)

        self.data = {}
        self._filter_data(json_data, self._schema['properties'], self.data)
        self.validator = Draft4Validator(self._schema)
        self.errors = None

    def validate(self):
        try:
            self.validator.validate(self.data, self._schema)
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
    def fields(self):
        fields = []
        propertries = self._schema['properties']
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
            "extra_classes": ["example_class", ]
        },
    },
    "required": ['to_uid', ],
}


def test():
    form_data = {"to_uid": "fuck"}
    form = JsonForm(json_data={}, live_schema=_schema)
    for field in form.fields:
        print field.render()
    form = JsonForm(json_data=form_data, live_schema=_schema)
    if not form.validate():
        print form.errors

if __name__ == "__main__":
    test()