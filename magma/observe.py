try:
    # Attempt to import the 'observe' decorator from langfuse.
    # We alias it as 'trace' to provide a consistent API under the magma namespace.
    from langfuse import observe as trace
except ImportError:
    # If langfuse is not installed, create a dummy decorator.
    # This allows the magma library to be imported and used without langfuse,
    # though tracing features will be disabled.
    print("Warning: 'langfuse' package not found. Tracing will be disabled. "
          "Install with 'pip install langfuse'.")
    
    def dummy_decorator(*args, **kwargs):
        # If called as @trace, it takes the function and returns it unwrapped.
        if args and callable(args[0]):
            return args[0]
        # If called as @trace(...), it returns a decorator that does nothing.
        else:
            def no_op(func):
                return func
            return no_op
            
    trace = dummy_decorator

# You can also add other observability-related utilities here in the future.
__all__ = ['trace']