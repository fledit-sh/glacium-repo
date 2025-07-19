Run
===

:class:`glacium.api.Run` is a small container describing a single
simulation case.  All mutator methods return the instance itself so
calls can be chained fluently.  The behaviour of each method is defined
in ``tasks.md``.  Key operations are summarised below.

Fluent mutators
---------------

``select_airfoil(name)``
    Set or change the airfoil identifier.

``set(key, value)``
    Store one scalar parameter.

``set_bulk(mapping)``
    Add several parameters at once.

``add_job(name)``
    Append a job string. Duplicates are allowed.

``jobs(iterable)``
    Extend the job list with multiple names.

``clear_jobs()``
    Remove **all** previously added jobs.

``tag(label)``
    Add a single tag to the ``tags`` set.

``tags(iterable)``
    Add many tags.

``remove_tag(label)``
    Delete a tag if present.

``depends_on(other)``
    Declare a hard dependency to another run.

``clone(deep=True)``
    Return an independent copy. Dependency edges are not duplicated.

Utility methods
---------------

``preview(fmt="str")``
    Return a human readable snapshot of the current state.

``validate()``
    Raise an error if mandatory data is missing or inconsistent.

``to_dict()`` / ``to_json()`` / ``to_yaml()``
    Serialise only declarative state without attached results.

``from_dict(mapping)``
    Recreate a run from serialised data.

``load(uid)``
    Load an existing project by UID and return a :class:`~glacium.api.Project`.

For the authoritative specification see lines 1–93 of
``tasks.md``.