# coding: utf-8
import json
import jsonschema
from jsonschema.validators import Draft4Validator
from json_form import BaseField

class UserExtraField(BaseField):
    default_template = '''
    <span class="form-title">{{name}}</span>
    <input type="{{input_type}}" class="form-field {extra_classes}" name="{{input_name}}" value="{{input_value}}" id="{{input_id}}" placeholder="{{input_holder}}"/>
    '''

    def __init__(
            self, name, input_type, input_name,
            input_id=None, extra_classes=None, input_holder="", input_value=""):
        super(UserExtraField, self).__init__(name, input_type, input_name, input_id, extra_classes, input_holder, input_value)

    def render(self):
        return self.default_template.format(
            name=self.name,
            input_type=self.input_type,
            input_name=self.input_name,
            input_id=self.input_id,
            extra_classes=" ".join(self.extra_classes),
            input_holder=self.input_holder,
            input_value=self.input_value,
        )

def create_item(t, name, input_name, holder="", pattern="", options=[]):
    item = {"type":t, "name": name, "input_name": input_name, "holder":holder, "pattern": pattern, "options": options}
    return item

def create_basketball():
    items = []
    items.append(create_item("string", u"群昵称", u"groupname"))
    items.append(create_item("string", u"球衣号码", u"ball_number", pattern="\d+"))
    items.append(create_item("options", u"球场位置", u"ball_position", options=[u"得分后卫", u"组织后卫", u"小前锋", u"大前锋", u"中锋", u"啦啦队"]))
    print json.dumps(items)

if __name__ == "__main__":
    create_basketball()
