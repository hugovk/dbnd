from dbnd import parameter
from dbnd._core.decorator.task_decorator_spec import build_task_decorator_spec


class TestTaskDecoratorSpecPy3(object):
    def test_annotations(self):
        def with_annotations(a: int, b: str, **kwargs: str) -> int:
            pass

        decorator_spec = build_task_decorator_spec(with_annotations, {}, parameter)
        assert decorator_spec.annotations == {
            "return": int,
            "a": int,
            "b": str,
            "kwargs": str,
        }
        assert decorator_spec.doc_annotations == {}

    def test_args_and_kwargs(self):
        def args_and_kwargs(a, *args, word="default", **kwargs):
            pass

        decorator_spec = build_task_decorator_spec(args_and_kwargs, {}, parameter)
        assert not decorator_spec.is_class
        assert decorator_spec.args == ["a"]
        assert decorator_spec.varargs == "args"
        assert decorator_spec.varkw == "kwargs"
        assert decorator_spec.defaults == {}
        assert decorator_spec.kwonlyargs == ["word"]
        assert decorator_spec.kwonlydefaults == {"word": "default"}
        assert decorator_spec.defaults_values == ()
        assert decorator_spec.name == "args_and_kwargs"

        assert decorator_spec.known_keywords_names == {"a"}

    def test_args_and_kwargs_and_decorator_kwarg(self):
        def args_and_kwargs(a, *args, word="default", **kwargs):
            pass

        decorator_spec = build_task_decorator_spec(
            args_and_kwargs, {"decorator": 1}, parameter
        )
        assert not decorator_spec.is_class
        assert decorator_spec.args == ["a"]
        assert decorator_spec.varargs == "args"
        assert decorator_spec.varkw == "kwargs"
        assert decorator_spec.defaults == {}
        assert decorator_spec.decorator_kwargs == {"decorator": 1}
        assert decorator_spec.kwonlyargs == ["word"]
        assert decorator_spec.kwonlydefaults == {"word": "default"}
        assert decorator_spec.defaults_values == ()
        assert decorator_spec.name == "args_and_kwargs"

        assert decorator_spec.known_keywords_names == {"a", "decorator"}
