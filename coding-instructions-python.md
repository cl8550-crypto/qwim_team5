---
applyTo: '**/*.py'
---

<!-- PROTECTED:BEGIN: all-protected-sections -->
Start of protected sections (their content should not be changed unless there are very compelling reasons explicitly stated)

# Main instructions 

## Use Thrifty Socratic prompting

You are a Thrifty Socratic analyst. Your first priority is to remove ambiguity, and answer only after you are completely sure of request details and requirements, after checking with me when not sure of your assumptions.  

The following standards must be applied to interactions with all coding agents, including Github Copilot, Claude Code, OpenCode, Cursor, Codex.

Coding agents must follow these standards when creating or editing code:

- Use a smallest high-impact output approach
- For each step taken by the coding agent, provide explicitly the token usage by LLMs and coding agents, accurately measured using a tiered approach
  - use provider-reported usage returned by actual LLM API response whenever available
  - use LiteLLM acount_tokens() for pre-call counting
  - use tiktoken directly when the coding agent uses OpenAI tokenization
- Provide the minimum response that still preserves intent, correctness and decision value.
- Keep the user's goal, constraints, assumptions, and important tradeoffs intact.
- Default structure:
  - objective: what the task is trying to achieve
  - key context: only context needed to avoid losing or wasting tokens
  - proposed action or solution: concise and practical
  - risks and edge cases: be comprehensive, yet primarily focus on material ones
- Prioritize:
  - accuracy over brevity
  - actionability over explanation
  - preserving business and technical intent over saving tokens
  - explicit assumptions when they affect implementation
  - small clarifying questions only when necessary and you are not completely sure
- Python codes should strictly follow my coding instructions and standards (see file `coding-instructions-python.md`).
- Place emphasis on easy-to-understand Python codes and corresponding documentation, docstrings and 
   comments.
- To the largest extent possible, choose and implement numerical methods and Python codes focused on high computational performance
- The Python codes should focus on code modularity and reusability, while retaining code
   simplification as much as possible
- Using my coding instructions and standards, document Python functions and classes by emphasizing clarity and ease of understanding
- Use object-oriented programming when you need **state management**, **polymorphism**, or **domain modeling**
- Use functional programming for **data transformations**, **pure calculations**, and **pipelines**
- Ask questions if you are not completely sure whether to use object-oriented programming or functional programming for any programming task in Python, including implementation of numerical methods or quantitative models, providing details on advantages and disadvantages for each approach
- Ensure that all my Python classes are written using Python package `attrs`, including keyword-only attributes, explicit attribute declaration, validation and conversion. Enum classes, Exception classes, and TypedDict subclasses should be excluded from using "attrs"
- Ensure that all my Python functions (except Shiny framework-mandated callbacks) only use keyword-only arguments, such that function parameters can only be specified using their names during a function call. Use `*` marker in a function signature to specify keyword-only arguments. When `*` is used, all parameters defined after it must be passed as keyword arguments. Only functions with 2+ parameters should get `*` for consistency.
- Shiny framework-mandated callbacks should be excluded from the keyword-only rule, since they have fixed positional signatures dictated by the Shiny reactive framework.
- Run the Python codes using Python packages already installed in virtual environment (usually in folder .venv)

Make sure to incorporate all 3 phases described below.
Phase 1: Only questions and clarifications:
Ask the minimum set of clarifying questions needed to produce a correct, context-specific answer. Each question must be tied to a concrete decision the answer depends on (such as metrics, constraints, scope, time window, audience, risk tolerance). Do not provide recommendations yet.

Phase 2: Assumptions check:
After I provide answers to your clarifying questions, restate the problem in your own words, and list all assumptions you are making. Include assumptions derived from my requests and my answers to your clarifying questions, and also  assumptions you deem important. If something is still missing or not fully clear, ask follow-up questions as needed. After stating the assumptions, please ask me to confirm (or edit) these assumptions, and do not proceed to step 3 (Answer and implementation) until I have explicitly agreed with all stated assumptions.

Phase 3: Answer and Implementation:
Provide your answer only when the problem is fully specified and you are completely sure of my requirements. Include explanations and at least one alternative framing that could change the recommendation. Python codes should strictly follow my coding instructions and standards (see file `coding-instructions-python.md`). Place emphasis on easy-to-understand Python codes and corresponding documentation, docstrings and comments. To the largest extent possible, choose and implement numerical methods and Python codes focused on high computational performance. The Python codes should focus on code modularity and reusability, while retaining code simplification as much as possible. Using my coding instructions and standards, document Python functions and classes by emphasizing clarity and ease of understanding.

Ask first clarifying questions, as much as needed. Think carefully and step-by-step before responding; this problem is harder than it looks. After making code changes, summarize which functions and files were updated. Create or update any pytest tests associated to these code changes, such that test line coverage is at least 90% and branch coverage is as close as possible to 100%. Create or update documentation and docstrings, properdocs related comments, and properdocs related files to be consistent with coding changes.  Make sure to incorporate my coding instructions (see file `coding-instructions-python.md`) and coding best practices. If you are not completely sure, please ask. Make sure you follow Phase 1, Phase 2 and Phase 3 as a Socratic analyst. If you encounter defensive branches or edge cases that are unreasonably difficult to test without extensive dependency mocking or code refactoring, apply `# pragma: no cover` to those specific code lines or  branches.

Inspect the relevant code files first. Always use 'head' or 'tail' and 'grep' when running shell commands with potentially a lot of output and filter shell output for exactly what you need.

The expectation is that test line coverage is at least 90%, while branch coverage is as close as possible to 100%. Add or update tests to ensure that each non-excluded Python file in the codebase has sufficient coverage for all relevant categories of tests: unit tests, integration tests, regression tests, behavioral tests, hypothesis tests, acceptance (robot framework) tests.

Comprehensive information on current testing coverage is provided in file `index.html` in folder `htmlcov` and in file `coverage.json` in main project folder. Unless explicitly approved by me, do not regenerate yourself these files for overall coverage testing of the entire codebase, since these testing coverage files will be generated by me explicitly running the corresponding commands.

## Use the Python virtual environment in .venv

You may need to activate it by using the Python command `.venv\Scripts\Activate`
The virtual environment in folder `.venv` is generated using `uv add polars` using `pyproject.toml`
Do not install packages; always rely on packages made available in virtual environment in folder `.venv`

## Coding standards and naming conventions for names of variables and functions used in Python codes

- These conding standards and naming conventions take precedence over all other coding instructions.
- Any Python file should have less than one thousand lines of code. If it has more than 1000 lines of code, it should be refactored into multiple Python files, each file with no more thn 1000 lines of code.
- Use `snake_case_with_underscores` for variable and function names. Example: `calculate_interest` and `total_amount`. Exceptions: when the name includes an acronym, in which case the acronym should be in uppercase (examples: client_QWIM or calculate_CAGR, where QWIM = Quantitative Weallth and Investment Management and CAGR = Compound Annual Growth Rate); when the name includes JSON (examples: `format_as_JSON` or `JSON_enabled`)
- Variable names should be written from more general (to the left) to more specific (as specifiers are added to the variable name to the right), unless explicitly specified otherwise. Examples: `estimator_distribution_univariate_lognormal` and `estimator_distribution_univariate_normal`
- Function names should be written from more general (to the left) to more specific (as specifiers are added to the function name the right), unless explicitly specified otherwise. Examples: `calc_estimator_distribution_univariate_lognormal` and `calc_estimator_distribution_univariate_normal`
- Use `CamelCase_with_underscores` for class names. Examples: `Investment_Portfolio` and `Retirement_Calculator` and `Formatter_Human_Readable`. The exception is when the name includes an acronym, in which case the acronym should be in uppercase (examples: `Formatter_Structured_JSON` or  `Client_QWIM` or `Calculator_CAGR`, where QWIM = Quantitative Weallth and Investment Management and CAGR = Compound Annual Growth Rate)
- Any variable name should include at least 3 (three) characters, and should be descriptive. If you need to use an upper case letter in the variable name, make sure that variable name does not start with upper case. If necessary, start variable name using `value_` or `temp_` or similar. Acceptable: value_QWIM. Not acceptable: QWIM_value
- Use `CamelCase_with_underscores` for exception names and error handling. The name should start with Exception. Example: `Exception_Invalid_Input` and `Exception_Data_Not_Found`
- Use `UPPERCASE_with_underscores` for constants and enums. Example: `MAX_RETRY_ATTEMPTS` and `ANNUITY_TYPE`
- Use `lowercase_with_underscores` for module names. Example: `data_processing` and `user_interface`. The exception is when the name includes an acronym, in which case the acronym should be in uppercase (examples: Client_QWIM or Calculate_CAGR, where QWIM = Quantitative Weallth and Investment Management and CAGR = Compound Annual Growth Rate)
- Use `lowercase_with_underscores` for package names.
- Use `snake_case_with_underscores` for file names, including names of files implementing  tabs and subtabs for a Shiny dashboard. Examples `tab_clients` and `subtab_personal_info`
- For names of unit test files, use `test_unit_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_unit`(same subfolder structure within `tests\tests_unit` folder as within `src` folder). Examples: unit tests for a file named `utils_portfolio.py` in folder `src\portfolios` would be stored in file named `test_unit_utils_portfolio.py` in folder `tests\tests_unit\src\portfolios`; unit tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_unit_subtab_personal_info.py` in folder `tests\tests_unit\dashboard\shiny_tab_clients`.
- For names of regression test files, use `test_regression_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_regression`(same subfolder structure within `tests\tests_regression` folder as within `src` folder). Examples: regression tests for a file named `utils_portfolio.py` in folder `src\portfolios` would be stored in file named `test_regression_utils_portfolio.py` in folder `tests\tests_regression\src\portfolios`; regression tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_regression_subTab_Personal_Info.py` in folder `tests\tests_regression\dashboard\shiny_tab_clients`
- For names of integration test files, use `test_integration_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_integration`(same subfolder structure within `tests\tests_integration` folder as within `src` folder). Examples: integration tests for a file named `utils_portfolio.py` in folder `src\portfolios` would be stored in file named `test_integration_utils_portfolio.py` in folder `tests\tests_integration\src\portfolios`; unit tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_integration_subtab_personal_info.py` in folder `tests\tests_integration\dashboard\shiny_tab_clients`.
- For names of Shiny dashboard test files, use `test_shiny_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_shiny`(same subfolder structure within `tests\tests_shiny` folder as within `src` folder). Example: shiny tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_shiny_subtab_personal_info.py` in folder `tests\tests_shiny\dashboard\shiny_tab_clients`.
- For names of behave test files, use `test_behave_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_behave`(same subfolder structure within `tests\tests_behave` folder as within `src` folder). Examples: behave tests for a file named `utils_portfolio.py` in folder `src\portfolios` would be stored in file named `test_behave_utils_portfolio.py` in folder `tests\tests_behave\src\portfolios`; behave tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_behave_subtab_personal_info.py` in folder `tests\tests_behave\dashboard\shiny_tab_clients`.
- For names of hypothesis test files, use `test_hypothesis_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_hypothesis`(same subfolder structure within `tests\tests_hypothesis` folder as within `src` folder). Examples: hypothesis tests for a file named `utils_portfolio.py` in folder `src\portfolios` would be stored in file named `test_hypothesis_utils_portfolio.py` in folder `tests\tests_hypothesis\src\portfolios`; hypothesis tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_hypothesis_subtab_personal_info.py` in folder `tests\tests_hypothesis\dashboard\shiny_tab_clients`.
- For names of Robot Framework test files, use `test_robot_fmk_` prefix followed by the module name. The test file is stored in a subfolder within `tests\tests_robot_framework`(same subfolder structure within `tests\tests_robot_framework` folder as within `src` folder). Examples: Robot Framework tests for a file named `utils_portfolio.py` in folder `src\portfolios` would be stored in file named `test_robot_utils_portfolio.py` in folder `tests\tests_robot\src\portfolios`; Robot Framework tests for a file named `subtab_personal_info.py` in folder `src\dashboard\shiny_tab_clients` would be stored in file `test_robot_subtab_personal_info.py` in folder `tests\tests_robot\dashboard\shiny_tab_clients`.
- For names of test functions, use `CamelCase_with_underscores`. The name of the function should start with `Test_` followed by words (separated by underscores) describing what needs to be tested. Example: `Test_Annuity_SPIA_Withdrawal_Rates` instead of `TestAnnuitySPIAWithdrawal_Rates`  and `Test_Portfolio_Data_Validation` instead of `TestPortfolioDataValidation`. The words in the name of the test function need to be separated by underscores `_`. For acronyms such as QWIM or SPIA or VA or RILA use capital letters. 
- For names of classes implemented in test files, use `CamelCase_with_underscores`. The name of the testing class should start with `Class_Test_` followed by words (separated by underscores) describing what needs to be tested. Example: `Class_Test_Longevity_Model_Constant_Construction` instead of `TestLongevityModelConstantConstruction`  and `Class_Test_Portfolio_Data_Validation` instead of `TestPortfolioDataValidation`. The words in the name of the test class need to be separated by underscores `_`. For acronyms such as QWIM or SPIA or VA or RILA use capital letters. 
- For regression tests, use Parquet file to store data that is used to compare results obtained using the current version of the codebase versus the previous version of the codebase
- Use descriptive names that clearly indicate purpose of variable or function.
- Use a consistent naming scheme throughout the codebase, as described in my coding instructions.
- For lists, dictionaries and dataframes, use the snake case with upper case first letters for the elements. For example, an element "component_one" would be named "Component_One".
- Every variable name should have at least three characters. Variable names used in loops should have a descriptive name. For example, instead of loop written as `for (i in 1:10)`, the loop should be written as `for (idx in 1:10)`. Use either idx_shortname or item_shortname for loop variable names. For example, instead of `for (col in 1:num_cols)` use `for (idx_col in 1:num_cols)` or `for (item_col in 1:num_cols)`
- Unless explicitly or approved requested by me, please do not change the names of variables or functions in the codebase. If you think a variable name or function name is not clear or does not conform to my coding instructions and instructions, please open an issue to discuss it.
- Ensure two empty rows are in the Python file before each function definition.
- For exception handling use exception-related classes and functions from Python file "exception_custom.py" stored in folder `src\utils\custom_exceptions_errors_loggers`.
- Do not use any print statements for logging or debugging. Instead use functions and classes from Python file "logger_custom.py" stored in folder `src\utils\custom_exceptions_errors_loggers`.
- Names of variables, functions, enums associated with "custom exception" Python classes (explicitly implemented by me in folder `src\utils\custom_exceptions_errors_loggers`) should use `CamelCase_with_underscores`. Examples: use `Data_Validation_Error` instead of `DataValidationError`; use `Config_Error` instead of `ConfigError`; use `Exception_Insufficient_Holdings` instead of `ExceptionInsufficientHoldings`
- Unless explicitly requested otherwise, any existing print messages should be replaced by functions from Python file "logger_custom.py" in stored folder `src\utils\custom_exceptions_errors_loggers`
- Do not use reserved names (either in native Python or in Python packages) for any variable name or function name that I am adding to the codebase
- For classes designed primarily to store data, use `@dataclass` decorator to convert a standard class into a data class.
- Do not perform equality checks with floating point values.
- Use modern, recommended Python packages and infrastructure for numerical methods. Focus on high computational performance. For example, use numpy.random.Generator (as the modern, recommended infrastructure) for random sampling instead of np.random functions, which is the traditional (legacy) approach.
- Use pure functions (Functions that do not modify their arguments or produce any other side-effects) as much as possible, and describe why and when not possible to use pure functions.
- Avoid side effects in functions. Do not implement non-pure functions without asking me. Please let me know in all situations when this is not possible.
- Use Python library `aenum`, instead of built-in Python enumeration class Enum, to create and manage enumerati
- Use input validation (with early returns), configuration validation, business logic validation and defensive programming as the primary approach, with try-except reserved for truly unpredictable operations
- Ensure that all my Python classes are written using Python package `attrs`, including keyword-only attributes, explicit attribute declaration, validation and conversion. Enum classes, Exception classes, and TypedDict subclasses should be excluded from using "attrs".
- Ensure that all my Python functions (except Shiny framework-mandated callbacks) only use keyword-only arguments, such that function parameters can only be specified using their names during a function call. Use `*` marker in a function signature to specify keyword-only arguments. When `*` is used, all parameters defined after it must be passed as keyword arguments. Only functions with 2+ parameters should get `*` for consistency.
- Shiny framework-mandated callbacks should be excluded from the keyword-only rule, since they have fixed positional signatures dictated by the Shiny reactive framework.
- When a function has at least 2 input arguments, the function signature needs to have only one input argument per row, starting with second row after function name.
- Use Python package `pydantic` (and pydantic family of Python packages) for parameters and data validation.
- Do not use any non-Python (including TypeScript) codes unless explicitly requested; instead use Python codes that would provide similar requested functionalities and capabilities.

## Standards for coding agents

These standards apply to all coding agents, including Github Copilot, Claude Code, OpenCode, Cursor, Codex.

Coding agents must follow these standards when creating or editing code:

- Use a smallest high-impact output approach
- For each step taken by the coding agent, provide explicitly the token usage by LLMs and coding agents, accurately measured using a tiered approach
  - use provider-reported usage returned by actual LLM API response whenever available
  - use LiteLLM acount_tokens() for pre-call counting
  - use tiktoken directly when the coding agent uses OpenAI tokenization
- Provide the minimum response that still preserves intent, correctness and decision value.
- Do not reduce output to terse fragments or "caveman" summaries
- Keep the user's goal, constraints, assumptions, and important tradeoffs intact.
- Default structure:
  - objective: what the task is trying to achieve
  - key context: only context needed to avoid losing or wasting tokens
  - proposed action or solution: concise and practical
  - risks and edge cases: be comprehensive, yet primarily focus on material ones
- Prioritize:
  - accuracy over brevity
  - actionability over explanation
  - preserving business and technical intent over saving tokens
  - explicit assumptions when they affect implementation
  - small clarifying questions only when necessary and you are not completely sure
- Python codes should strictly follow my coding instructions and standards (see file `coding-instructions-python.md`).
- Place emphasis on easy-to-understand Python codes and corresponding documentation, docstrings and comments.
- To the largest extent possible, choose and implement numerical methods and Python codes focused on high computational performance
- The Python codes should focus on code modularity and reusability, while retaining code simplification as much as possible
- Using my coding instructions and standards, document Python functions and classes by emphasizing clarity and ease of understanding
- Use object-oriented programming when you need **state management**, **polymorphism**, or **domain modeling**
- Use functional programming for **data transformations**, **pure calculations**, and **pipelines**
- Ask questions if you are not completely sure whether to use object-oriented programming or functional programming for any programming task in Python, including implementation of numerical methods or quantitative models, providing details on advantages and disadvantages for each approach
- Run the Python codes using Python packages already installed in virtual environment (usually in folder .venv)

## Object-Oriented Programming (OOP) and when to Use OOP

Use object-oriented programming when you need **state management**, **polymorphism**, or **domain modeling**:

### Core OOP Principles

- Prefer composition over inheritance by default
- Encapsulate state with private attributes (use `m_` prefix per project standards)
- Expose a small, explicit public interface on each class (API principle)
- Apply SOLID principles, especially Single Responsibility and Dependency Inversion
- Avoid global state and free functions unless they are:
  - Small, pure mathematical helpers
  - Entrypoints (e.g., `main()` function in scripts)

### When OOP is Appropriate in QWIM

| Use Case | Example | Why OOP |
| ---------- | --------- | -------- |
| Domain entities | `Portfolio_QWIM`, `Client_QWIM` | Encapsulate state and behavior |
| Stateful calculations | `Monte_Carlo_Simulator` | Maintain simulation state across iterations |
| Strategy variations | `Rebalancing_Strategy` hierarchy | Polymorphism for different algorithms |
| Resource management | `Market_Data_Connection` | Control lifecycle (open/close) |
| Configuration holders | `Risk_Parameters` | Group related settings |

## Functional Programming (FP) and when to use FP

Use functional programming for **data transformations**, **pure calculations**, and **pipelines**:

### Core Functional Programming Principles

- Prefer pure functions (no side effects, deterministic output)
- Use immutable data structures where possible
- Compose small functions into larger pipelines
- Avoid shared mutable state
- Use higher-order functions (map, filter, reduce)

### When FP is Appropriate in QWIM

| Use Case | Example | Why FP |
| ---------- | --------- | -------- |
| Data transformations | Price normalization, returns calculation | Pure, composable operations |
| Mathematical formulas | Black-Scholes pricing, Greeks | Deterministic, testable |
| Data pipelines | ETL workflows, report generation | Sequential transformations |
| Filtering/mapping | Portfolio screening, risk filtering | Declarative, readable |
| Aggregations | Performance metrics, risk summaries | Reduce operations |

## Python coding standards

### Code linting and formatting

- Ensure that the generated code is consistent with Python package `ruff` requirements specified in "pyproject.toml"

### Type checking

- Use Python packages `ty` for type checking. Ensure that the generated code is consistent with Python package `ty` requirements specified in "pyproject.toml". Also use Python packages `pyright` and `pyrefly` as static type checkers.

### Core Standards

- For exception handling use exception-related classes and functions from Python file "exception_custom.py" stored in folder `src\utils\custom_exceptions_errors_loggers`.
- Do not use any print statements for logging or debugging. Instead use functions and classes from Python file "logger_custom.py" stored in folder `src\utils\custom_exceptions_errors_loggers`.
- Unless explicitly requested otherwise, any existing print messages should be replaced by functions from Python file "logger_custom.py" in stored folder `src\utils\custom_exceptions_errors_loggers`
- Do not use reserved names (for functions either in Python or in Python packages) for any variable name in the generated codes
- Use pure functions (Functions that do not modify their arguments or produce any other side-effects) as much as possible, and describe why and when not possible to use pure functions.
- Avoid side effects in functions. Do not implement non-pure functions without asking me. Please let me know whenever this is not possible.
- Use Python library aenum, instead of built-in Enum, to create and manage enumerations
- Use input validation (with early returns), configuration validation, business logic validation and defensive programming as the primary approach, with try-except reserved for truly unpredictable operations
- When a function has at least 2 input arguments, the function signature needs to have only one input argument per row, starting with second row after function name.
- Use Python package `pydantic` (and pydantic family of Python packages) for parameters and data validation.
- Do not use any JavaScript codes unless explicitly requested; instead use Python codes that would provide similar requested functionalities and capabilities.

## Data structures should be based on Polars DataFrames

Use Polars for every tabular workflow in this project, including tabular data structures and time series. Never introduce pandas into application logic. The only acceptable pandas boundary is an external library API that cannot consume Polars directly, and that boundary must be isolated and documented.

Rely on the following core rules when using Polars

- Design schemas before loading data.
- Keep `Date` as the first column for time series.
- Use `Title_Case` for DataFrame column names.
- Prefer expressions and lazy pipelines over Python loops.
- Treat null handling as an explicit design decision.
- Clone caller-owned DataFrames before mutation.
- Stream large pipelines with `scan_*`, lazy expressions, and `collect(engine="streaming")` when appropriate.

End of protected sections (their content should not be changed unless there are very compelling reasons explicitly stated)
<!-- PROTECTED:END: all-protected-sections -->

---

## Table of Contents

- [Zone 1: Polars Deep-Dive](#zone-1-polars-deep-dive)
- [Zone 2: Testing Patterns](#zone-2-testing-patterns)
- [Zone 3: Custom Logger and Exception Usage](#zone-3-custom-logger-and-exception-usage)
- [Zone 4: Shiny Dashboard Architecture](#zone-4-shiny-dashboard-architecture)
- [Zone 5: Security and Validation](#zone-5-security-and-validation)
- [Zone 6: Performance Patterns](#zone-6-performance-patterns)
- [Zone 7: Documentation and ProperDocs](#zone-7-documentation-and-properdocs)
- [Zone 8: Modern Python 3.12+ Typing](#zone-8-modern-python-312-typing)
- [Zone 9: Concurrency and Parallelism](#zone-9-concurrency-and-parallelism)
- [Zone 10: Cross-Platform Windows, Linux, and Posit Connect](#zone-10-cross-platform-windows-linux-and-posit-connect)
- [Zone 11: Typst and PDF Reporting](#zone-11-typst-and-pdf-reporting)
- [Appendix A: Protected-Section Recommendations](#appendix-a-protected-section-recommendations)

---

## Zone 1: Polars Deep-Dive

This zone provides authoritative, project-wide guidance for every Polars workflow in the QWIM codebase, covering lazy pipelines, schema design, joins, window functions, streaming sinks, and partitioned datasets â€” the complete vocabulary a coding agent needs to write correct, performant, Arrow-native code from first principles without ever reaching for pandas.

### Zone 1 mandatory rules

1. Every tabular workflow uses Polars; the only permitted pandas boundary is an external-library API that physically cannot consume a Polars frame, and that boundary must be wrapped in an adapter function with a `# pandas-boundary` comment explaining the necessity.
2. Define a `pl.Schema` or typed `dict[str, pl.DataType]` constant before reading any file; validate immediately after `read_*` or `scan_*` by checking `set(EXPECTED_SCHEMA) <= set(data_frame.columns)` and raising `Exception_Data_Validation_Error` on failure.
3. Keep `Date` (type `pl.Date`) as the first column in every time-series frame; sort by it after every load, filter, or join that could reorder rows.
4. Prefer `pl.LazyFrame` for any pipeline with more than one transformation step; call `.collect()` only once at the end, and use `collect(engine="streaming")` when the data volume may exceed available RAM.
5. Express every conditional, mapping, or rolling calculation as a Polars expression (`pl.col()`, `pl.when().then().otherwise()`, `.rolling_mean()`, `.over()`) rather than iterating rows in Python â€” row-by-row iteration defeats SIMD and multi-threading.
6. Apply predicate pushdown explicitly by placing `.filter()` calls as early as possible in a `LazyFrame` pipeline; projection pushdown works similarly with `.select()` before costly joins.
7. Use `pl.Enum` for any column whose valid values are known at design time; use `pl.Categorical` only for values discovered dynamically from data.
8. Represent missing values with `null` (never with `float('nan')` or sentinel integers); handle them explicitly with `.fill_null()`, `.drop_nulls()`, or `.is_null()` â€” never let nulls propagate silently into arithmetic.
9. Use `.clone()` before mutating a DataFrame that was passed as a function argument; never modify caller-owned data in place.
10. Use `pl.UInt8` / `pl.UInt16` for non-negative counts and ages; `pl.Float64` for prices and returns; `pl.Decimal` only for exact-money reporting where rounding control is legally required.
11. Store nested or heterogeneous fields in `pl.Struct` columns rather than Python dicts or expanding to wide sparse tables â€” `Struct` keeps data inside Arrow memory and exposes `.struct.field()` expressions for vectorised access.
12. Use `join_asof` for market-data lookups where timestamps rarely align exactly; always sort both frames by the join key before calling it, and document the `strategy` parameter choice (`"backward"`, `"forward"`, or `"nearest"`).
13. Use `sink_parquet()` with `compression="zstd"` for streaming writes to disk; never call `.collect().write_parquet()` on a dataset that may exceed RAM.
14. Partition output datasets with `pl.PartitionByKey` on columns with cardinality between 5 and 100 (e.g., `risk_profile`, `asset_class`); avoid partitioning on high-cardinality columns like `client_id`.

### Canonical time-series pattern

```python
from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Data_Validation_Error,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)

# Schema constant defined once at module level â€” never inline inside functions.
SCHEMA_PORTFOLIO_TS: dict[str, pl.DataType] = {
    "Date": pl.Date,
    "Portfolio_Value": pl.Float64,
    "Benchmark_Value": pl.Float64,
}


def load_portfolio_time_series_QWIM(
    file_path: Path,
    window_rolling: int = 20,
) -> pl.DataFrame:
    """Load, validate, and enrich a portfolio time-series file.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to a CSV or Parquet file. CSV files must have a ``Date``
        column in ``YYYY-MM-DD`` format. All columns listed in
        ``SCHEMA_PORTFOLIO_TS`` must be present.
    window_rolling : int, optional
        Rolling-window size in trading days for the volatility column,
        by default ``20``.

    Returns
    -------
    polars.DataFrame
        Frame sorted by ``Date`` with additional columns:
        ``Daily_Return``, ``Rolling_Return_20D``, ``Rolling_Vol_20D``.
        Schema is guaranteed to match ``SCHEMA_PORTFOLIO_TS`` plus the
        three derived columns.

    Raises
    ------
    Exception_Data_Validation_Error
        Raised when required columns are absent after loading.

    Notes
    -----
    All transformations are pure (no side effects on the input file).
    The function logs an INFO message with the final row count.
    """
    # Read from file â€” choose reader based on suffix to avoid unnecessary parsing.
    if file_path.suffix.lower() == ".csv":
        data_frame = pl.read_csv(file_path).with_columns(
            pl.col("Date").str.strptime(pl.Date, format="%Y-%m-%d"),  # parse date string
        )
    else:
        data_frame = pl.read_parquet(file_path)

    # Validate schema at the module boundary; raise immediately on failure.
    missing_columns = [col for col in SCHEMA_PORTFOLIO_TS if col not in data_frame.columns]
    if missing_columns:
        raise Exception_Data_Validation_Error(
            "Required time-series columns are missing after load.",
            field="columns",
            value=missing_columns,
        )

    # Cast to declared types and sort â€” a single lazy plan for the full pipeline.
    result = (
        data_frame
        .cast(SCHEMA_PORTFOLIO_TS, strict=False)  # lenient cast; invalids become null
        .sort("Date")  # always sort after load
        .with_columns(
            pl.col("Portfolio_Value").pct_change().alias("Daily_Return"),
        )
        .with_columns(
            # Window functions stay inside the Polars engine â€” no Python loops.
            pl.col("Daily_Return").rolling_mean(window_size=window_rolling).alias("Rolling_Return_20D"),
            pl.col("Daily_Return").rolling_std(window_size=window_rolling).alias("Rolling_Vol_20D"),
        )
    )
    _logger.info("Loaded portfolio time series: %s rows, %s columns", result.height, result.width)
    return result
```

<!-- ANTIPATTERN -->
```python
# âŒ ANTI-PATTERN: row iteration for returns â€” never do this
import polars as pl

def calc_returns_slow(data_frame: pl.DataFrame) -> pl.DataFrame:
    """Anti-pattern: row-by-row Python loop defeats SIMD and multi-threading."""
    values = data_frame["Portfolio_Value"].to_list()  # pulls data into Python heap
    returns = []
    for idx in range(1, len(values)):  # O(n) Python interpreter overhead per row
        returns.append(values[idx] / values[idx - 1] - 1)
    returns.insert(0, None)
    return data_frame.with_columns(pl.Series("Daily_Return", returns))
```
<!-- /ANTIPATTERN -->

```python
# âœ… CORRECTED: vectorised expression â€” single SIMD pass
import polars as pl

def calc_returns_fast(data_frame: pl.DataFrame) -> pl.DataFrame:
    """Corrected pattern: Polars expression processed in Rust/SIMD, no Python loop."""
    return data_frame.with_columns(
        pl.col("Portfolio_Value").pct_change().alias("Daily_Return"),
    )
```

### Lazy pipeline with streaming

Use `LazyFrame` for any multi-step pipeline; use `collect(engine="streaming")` when the result might not fit in RAM. The streaming engine processes data in row-group batches and is particularly effective when combined with `sink_parquet()`.

```python
from __future__ import annotations

import numpy as np
import polars as pl

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def run_monte_carlo_streaming_QWIM(
    path_clients: str,
    path_market: str,
    num_scenarios: int,
    output_path: str,
    random_seed: int = 42,
) -> None:
    """Run a Monte Carlo simulation using Polars streaming for out-of-RAM datasets.

    Parameters
    ----------
    path_clients : str
        Path to a Parquet file containing client and instrument records.
    path_market : str
        Path to a Parquet file containing sorted market price history.
    num_scenarios : int
        Number of random scenario paths to simulate.
    output_path : str
        Destination Parquet path for simulation results.
    random_seed : int, optional
        Seed for the numpy random generator, by default ``42``.

    Returns
    -------
    None
        Results are written directly to ``output_path`` via streaming sink.

    Notes
    -----
    Uses ``numpy``'s seeded ``Generator`` for reproducible draws. Polars has
    no top-level ``pl.random()`` function; the idiomatic pattern is to generate
    draws with numpy and wrap in ``pl.Series`` before injecting into the pipeline.
    """
    rng = np.random.default_rng(seed=random_seed)
    # Pre-generate random fluctuations as a named Polars Series.
    fluctuations = pl.Series("fluctuation", rng.standard_normal(num_scenarios))

    pipeline = (
        pl.scan_parquet(path_clients)  # lazy scan â€” no data loaded yet
        .join_asof(
            pl.scan_parquet(path_market).sort("Timestamp"),  # must be sorted
            left_on="Sim_Time",
            right_on="Timestamp",
            by="Instrument_ID",  # apply asof match per instrument group
            strategy="backward",  # use latest available price before sim time
        )
        .filter(pl.col("Price").is_not_null())  # predicate pushdown: skip nulls early
        .with_columns(
            (pl.col("Price") * (1.0 + fluctuations)).alias("Sim_Payoff"),
        )
        .filter(pl.col("Sim_Payoff") > 0)  # business rule: discard negative payoffs
    )

    # Stream results directly to disk â€” avoids loading all scenarios into memory.
    pipeline.sink_parquet(
        output_path,
        compression="zstd",
        compression_level=3,
    )
    _logger.info("Monte Carlo streaming complete; results written to %s", output_path)
```

### Window functions and group-by-dynamic

```python
from __future__ import annotations

from datetime import date

import polars as pl

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def calc_rolling_risk_metrics_QWIM(
    data_frame: pl.DataFrame,
    group_col: str = "Risk_Profile",
    window_size: int = 20,
) -> pl.DataFrame:
    """Calculate per-group rolling risk metrics using Polars window functions.

    Parameters
    ----------
    data_frame : polars.DataFrame
        Frame with ``Date``, ``Daily_Return``, and ``group_col`` columns.
    group_col : str, optional
        Column name used for window partitioning, by default ``"Risk_Profile"``.
    window_size : int, optional
        Rolling window in trading days, by default ``20``.

    Returns
    -------
    polars.DataFrame
        Input frame enriched with ``Rolling_Vol`` and ``Rolling_Sharpe``
        columns computed independently within each ``group_col`` partition.

    Notes
    -----
    The ``over()`` expression is Polars' window function; it applies
    ``rolling_std`` within each group without a ``group_by`` + join round-trip.
    """
    return data_frame.with_columns(
        # .over(group_col) partitions the rolling calculation by group â€” no groupby needed.
        pl.col("Daily_Return")
        .rolling_std(window_size=window_size)
        .over(group_col)
        .alias("Rolling_Vol"),
        (
            pl.col("Daily_Return").rolling_mean(window_size=window_size).over(group_col)
            / pl.col("Daily_Return").rolling_std(window_size=window_size).over(group_col)
            * (252 ** 0.5)  # annualise: multiply daily Sharpe by sqrt(252 trading days)
        ).alias("Rolling_Sharpe"),
    )


def resample_monthly_QWIM(
    data_frame: pl.DataFrame,
) -> pl.DataFrame:
    """Resample a daily time series to monthly period returns.

    Parameters
    ----------
    data_frame : polars.DataFrame
        Sorted daily frame with ``Date`` (pl.Date) and ``Daily_Return`` columns.

    Returns
    -------
    polars.DataFrame
        Monthly frame with ``Period_Start`` (pl.Date) and ``Monthly_Return``
        columns computed as the arithmetic sum of daily returns within each month.

    Notes
    -----
    ``group_by_dynamic`` is the correct Polars idiom for time-windowed
    aggregations; it avoids a manual ``dt.year`` + ``dt.month`` groupby and
    respects calendar month boundaries automatically.
    """
    return (
        data_frame.sort("Date")
        .group_by_dynamic("Date", every="1mo")  # calendar-month buckets
        .agg(pl.col("Daily_Return").sum().alias("Monthly_Return"))
        .rename({"Date": "Period_Start"})
    )
```

### Polars data-type decision table

| Data | Recommended type | Why |
|---|---|---|
| Age, counts (0â€“255) | `pl.UInt8` | Smallest unsigned; saves memory in large frames |
| Age, counts (0â€“65535) | `pl.UInt16` | Still unsigned; handles large cohorts |
| Prices, returns, simulation values | `pl.Float64` | IEEE 754 double; matches numpy default |
| Exact money (fees, dividends) | `pl.Decimal` | 128-bit fixed precision; avoids float rounding |
| Risk profile, asset class | `pl.Enum` | Known-at-design-time; invalid values raise immediately |
| Discovered categories (e.g., sector from market feed) | `pl.Categorical` | Dictionary-encoded; cheaper than String at scale |
| Instrument struct fields | `pl.Struct` | Arrow-native grouping; avoids wide sparse tables |
| Scenario lists | `pl.List(pl.Float64)` | Variable-length per row; stays in Arrow memory |
| Flags | `pl.Boolean` | Bit-packed; 8 booleans per byte |

### Polars pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| `SchemaError: found invalid literal for dtype Float64` | CSV has missing values encoded as empty string, not `null` | Add `null_values=["", "NA", "N/A"]` to `read_csv` |
| `ColumnNotFoundError` after lazy `.collect()` | Projection pushdown removed a column used downstream | Add `.select(...)` after the step that introduces the column |
| Rolling result is all null | Window size exceeds frame height | Guard with `if data_frame.height >= window_size` |
| `join_asof` produces wrong matches | Left or right frame is not sorted on the join key | Call `.sort(join_key)` on both frames before the join |
| Memory spike despite `.lazy()` | An intermediate `.collect()` materialises the whole frame | Remove premature `.collect()` calls; stay lazy until final result |
| `sink_parquet` schema error | Output schema differs from inferred schema at sink time | Call `.cast(output_schema)` before `sink_parquet` |

*See also: Zone 6 (Performance) for lazy-pipeline optimisation; Zone 5 (Security) for file-path validation before `scan_parquet`.*

---

## Zone 2: Testing Patterns

This zone defines the authoritative testing strategy for the QWIM codebase. It covers all seven test categories (unit, integration, regression, hypothesis, Shiny, behave, Robot Framework), fixture design, Polars DataFrame assertion idioms, parametrise patterns, and the focused-first command discipline that keeps feedback loops under thirty seconds â€” because a test suite that takes five minutes will be skipped by both developers and coding agents.

### Zone 2 mandatory rules

1. Every source file under `src/` must have a corresponding unit-test file under `tests/tests_unit/` mirroring the same folder structure; a missing test file is treated as a coverage gap, not as an acceptable omission.
2. Test function names follow `Test_<Subject>_<Condition>_<ExpectedOutcome>` (CamelCase with underscores) and test class names follow `Class_Test_<Subject>` â€” never use bare `test_` prefix without a Subject.
3. Follow Arrange-Act-Assert (AAA) within every test function with a blank line between each phase; a test with no clear AAA boundary is considered improperly structured.
4. Use `pytest.mark.parametrize` for any test function that repeats the same assertion logic with different inputs â€” never write multiple near-identical test functions for different values.
5. Use `polars.testing.assert_frame_equal` and `polars.testing.assert_series_equal` for all Polars comparisons; never compare via `.to_pandas()` in test logic.
6. Regression baselines must be stored as Parquet files under `tests/tests_regression/baselines/`; exclude volatile fields (timestamps, process IDs, random identifiers) before comparison.
7. Hypothesis tests must use `@given` strategies covering the full valid domain and at least one boundary; document the invariant being tested in the docstring `Notes` section.
8. Behave feature files live under `tests/tests_behave/features/`; steps live in `tests/tests_behave/steps/`; both must be kept in sync with source changes.
9. Robot Framework test files use the `test_robot_fmk_` prefix; they live under `tests/tests_robot_framework/` mirroring the `src/` structure.
10. All conftest fixtures are documented with Numpydoc docstrings; a fixture without a `Returns` section is considered incomplete.
11. Use `pytest.approx` with an explicit `rel` or `abs` tolerance for all floating-point assertions; never use `==` on floats.
12. Apply `# pragma: no cover` only to genuinely impractical defensive paths (e.g., OS-level failures, unreachable platform branches); document the reason on the same line.

### Canonical unit-test pattern

```python
"""Unit tests for portfolio time-series loading utilities.

Test file location: tests/tests_unit/src/portfolios/test_unit_utils_portfolio_ts.py
Mirrors source:    src/portfolios/utils_portfolio_ts.py

Notes
-----
All tests are deterministic; no wall-clock dependencies.
Polars comparisons use ``polars.testing.assert_frame_equal`` exclusively.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Data_Validation_Error,
)


@pytest.fixture
def csv_portfolio_ts(tmp_path: Path) -> Path:
    """Write a minimal portfolio time-series CSV to a temp directory.

    Returns
    -------
    pathlib.Path
        Path to the written CSV file containing three rows of daily data
        with ``Date``, ``Portfolio_Value``, and ``Benchmark_Value`` columns.
    """
    content = "Date,Portfolio_Value,Benchmark_Value\n2024-01-01,100.0,99.0\n2024-01-02,101.5,99.8\n2024-01-03,102.0,100.1\n"
    file_path = tmp_path / "portfolio_ts.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def csv_missing_cols(tmp_path: Path) -> Path:
    """Write a CSV missing the required ``Benchmark_Value`` column.

    Returns
    -------
    pathlib.Path
        Path to the malformed CSV used for negative-path validation tests.
    """
    content = "Date,Portfolio_Value\n2024-01-01,100.0\n"
    file_path = tmp_path / "broken.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


class Class_Test_Load_Portfolio_Time_Series:
    """Tests for ``load_portfolio_time_series_QWIM``."""

    @pytest.mark.unit
    def Test_Returns_Correct_Schema_And_Row_Count(
        self,
        csv_portfolio_ts: Path,
    ) -> None:
        """Loading a valid CSV produces the expected schema and row count.

        Notes
        -----
        Verifies that ``Date`` is the first column, dtype is ``pl.Date``,
        and derived columns ``Daily_Return``, ``Rolling_Return_20D``,
        ``Rolling_Vol_20D`` are present.
        """
        # Arrange
        from src.portfolios.utils_portfolio_ts import load_portfolio_time_series_QWIM

        # Act
        result = load_portfolio_time_series_QWIM(csv_portfolio_ts)

        # Assert â€” schema and shape
        assert result.columns[0] == "Date", "Date must be the first column"
        assert result.schema["Date"] == pl.Date
        assert result.height == 3
        assert "Daily_Return" in result.columns

    @pytest.mark.unit
    def Test_Raises_On_Missing_Required_Column(
        self,
        csv_missing_cols: Path,
    ) -> None:
        """Loading a CSV without ``Benchmark_Value`` raises ``Exception_Data_Validation_Error``.

        Notes
        -----
        Validates the early-return guard at the module boundary.
        """
        # Arrange
        from src.portfolios.utils_portfolio_ts import load_portfolio_time_series_QWIM

        # Act & Assert
        with pytest.raises(Exception_Data_Validation_Error, match="missing"):
            load_portfolio_time_series_QWIM(csv_missing_cols)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("window_rolling", "expected_non_null_rows"),
        [
            (2, 1),   # 3 rows, window=2 â†’ 1 non-null rolling value
            (20, 0),  # 3 rows, window=20 â†’ all rolling values are null
        ],
        ids=["window_fits", "window_exceeds_data"],
    )
    def Test_Rolling_Window_Produces_Expected_Null_Count(
        self,
        csv_portfolio_ts: Path,
        window_rolling: int,
        expected_non_null_rows: int,
    ) -> None:
        """Rolling-window column produces the correct number of non-null values.

        Parameters
        ----------
        csv_portfolio_ts : pathlib.Path
            Fixture providing a 3-row CSV.
        window_rolling : int
            Rolling window size injected by parametrize.
        expected_non_null_rows : int
            Expected count of non-null entries in ``Rolling_Return_20D``.
        """
        # Arrange
        from src.portfolios.utils_portfolio_ts import load_portfolio_time_series_QWIM

        # Act
        result = load_portfolio_time_series_QWIM(csv_portfolio_ts, window_rolling=window_rolling)

        # Assert
        actual_non_null = result["Rolling_Return_20D"].drop_nulls().height
        assert actual_non_null == expected_non_null_rows
```

### Hypothesis property-based pattern

```python
"""Hypothesis tests for portfolio weight validation models.

File: tests/tests_unit/src/portfolios/test_unit_model_allocation.py
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Data_Validation_Error,
)


@given(
    weight_target=st.decimals(min_value=Decimal("0"), max_value=Decimal("1"), allow_nan=False),
    weight_current=st.decimals(min_value=Decimal("0"), max_value=Decimal("1"), allow_nan=False),
)
@settings(max_examples=200)
def Test_Allocation_Model_Accepts_All_Valid_Weight_Pairs(
    weight_target: Decimal,
    weight_current: Decimal,
) -> None:
    """Model_Allocation_Input_QWIM accepts any valid weight pair without raising.

    Notes
    -----
    Property: for all ``weight_target`` and ``weight_current`` in [0, 1] where
    ``|target - current| <= 0.5``, construction must succeed.
    """
    # Arrange
    from src.portfolios.model_allocation_input import Model_Allocation_Input_QWIM

    if abs(weight_target - weight_current) > Decimal("0.50"):
        pytest.skip("skip: change exceeds step limit â€” covered by negative test")

    # Act & Assert â€” must not raise
    model = Model_Allocation_Input_QWIM(
        ticker="AAPL",
        weight_target=weight_target,
        weight_current=weight_current,
    )
    assert model.ticker == "AAPL"
```

### Regression pattern with Parquet baseline

```python
"""Regression tests for monthly resampling utility.

File: tests/tests_regression/src/portfolios/test_regression_utils_portfolio_ts.py
"""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal


BASELINE_PATH = Path("tests/tests_regression/baselines/monthly_returns_baseline.parquet")


class Class_Test_Regression_Monthly_Resample:
    """Regression tests for ``resample_monthly_QWIM``."""

    @pytest.mark.regression
    def Test_Monthly_Resample_Matches_Baseline(
        self,
        tmp_path: Path,
    ) -> None:
        """Monthly resampling output matches stored Parquet baseline.

        Notes
        -----
        To update the baseline after an intentional algorithm change, delete
        ``BASELINE_PATH`` and re-run the test once; the missing-baseline branch
        will write the new file and skip assertion.
        """
        from src.portfolios.utils_portfolio_ts import resample_monthly_QWIM

        # Arrange â€” small deterministic input frame
        frame = pl.DataFrame({
            "Date": pl.date_range(
                start=pl.lit("2024-01-01").str.to_date(),
                end=pl.lit("2024-03-31").str.to_date(),
                interval="1d",
                eager=True,
            ),
        }).with_columns(
            pl.lit(0.001).alias("Daily_Return"),
        )

        # Act
        result = resample_monthly_QWIM(frame)

        if not BASELINE_PATH.exists():
            # First run â€” write baseline; no assertion yet.
            BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
            result.write_parquet(BASELINE_PATH)
            pytest.skip("Baseline written for the first time; re-run to assert.")

        # Assert â€” compare against stored baseline, excluding volatile metadata.
        baseline = pl.read_parquet(BASELINE_PATH)
        assert_frame_equal(result, baseline, check_exact=False, rtol=1e-6)
```

### Focused test commands

```powershell
# Run a single test file quickly (preferred first step)
python -m pytest tests/tests_unit/src/portfolios/test_unit_utils_portfolio_ts.py -q

# Branch coverage for one module
python -m coverage run --branch --include=src/portfolios/utils_portfolio_ts.py -m pytest tests/tests_unit/src/portfolios/test_unit_utils_portfolio_ts.py -q
python -m coverage report --show-missing

# Hypothesis tests (increase max_examples for thorough property checks)
python -m pytest tests/tests_unit/src/portfolios/test_unit_model_allocation.py -q --hypothesis-seed=0

# Behave acceptance test for a feature
behave tests/tests_behave/features/portfolios/portfolio_loading.feature

# Robot Framework smoke test for a module
robot tests/tests_robot_framework/src/portfolios/
```

### Testing pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| Test passes locally but fails in CI | Wall-clock dependency (`datetime.now()`) | Use `pytest-freezegun` to pin time |
| Flaky Polars assertion | `check_exact=True` on Float64 column | Use `assert_frame_equal(rtol=1e-6)` |
| Hypothesis test slow | Default `max_examples=100` with heavy fixture | Add `@settings(max_examples=30, deadline=None)` |
| Regression test fails after intentional change | Stale Parquet baseline | Delete baseline, re-run once to regenerate |
| Coverage gap on validation branch | Early-return guard never exercised | Add a parametrize case that triggers the guard |
| `Class_Test_` method not discovered by pytest | Method name starts with lowercase | Rename to `Test_<Subject>_<Condition>` |

*See also: Zone 1 (Polars) for `assert_frame_equal` options; Zone 3 (Logger) for asserting log output in tests.*

---

## Zone 3: Custom Logger and Exception Usage

This zone is the authoritative reference for the project's custom logging and exception system located in `src/utils/custom_exceptions_errors_loggers/`. It documents the public facades (`logger_custom`, `exception_custom`), structured usage patterns, secret masking, performance logging, audit logging, and the correct exception hierarchy â€” giving coding agents a complete, repo-grounded contract that prevents direct `loguru` imports and bare `print` statements anywhere in application code.

### Zone 3 mandatory rules

1. Application code must only import from the two public facades: `src.utils.custom_exceptions_errors_loggers.logger_custom` and `src.utils.custom_exceptions_errors_loggers.exception_custom`; private modules prefixed with `_` are for implementation and targeted unit tests only.
2. Obtain a module-level logger with `_logger = get_logger(__name__)` at module top-level, not inside functions; one logger per module, never shared across module boundaries.
3. Use lazy `%`-style formatting (`_logger.info("Loaded %s rows", n)`) not f-string interpolation inside log calls; the message string is only rendered if the log level is active, which avoids allocating strings for suppressed messages.
4. Bind structured context with `_logger.bind(client_id=cid)` before entering a multi-step workflow so all subsequent log records in that scope carry the context automatically without string concatenation.
5. Never log raw secrets, passwords, API keys, or PII; always mask with the logger infrastructure's masking helpers before structured logging.
6. Use `get_logger(__name__)` in every public module; never import `loguru` directly in application code.
7. Choose the lightest exception that preserves meaning from the project hierarchy: prefer `Exception_Data_Validation_Error` over the base `Exception_`; prefer `Exception_Validation_Input` for user-facing input errors; prefer `Exception_External_Service_Error` for third-party API failures.
8. Always chain exceptions with `raise Exception_... from exc` when re-raising inside a `try/except`; naked `raise Exception_...` in a `except` block loses the original traceback.
9. Do not use bare `except Exception:` clauses; catch the most specific exception type available, log it with `_logger.exception(...)`, and re-raise or raise a domain exception.
10. Use `tenacity` for retry logic on external calls; never write manual retry loops with `time.sleep` and `while` counters.
11. For performance-sensitive paths, use `@_logger.catch` (from the custom facade) or a context-manager timer that logs elapsed time at `DEBUG` level so production INFO streams are not polluted.

### Public facade import template

```python
"""Module docstring â€” always present, always Numpydoc style.

This module demonstrates the canonical import pattern for the custom
logging and exception system. All application modules follow this template.

Notes
-----
Never import from private modules (``_logger_handlers``, ``_exception_core``,
etc.) in application code. The public facades expose the full API.
"""
from __future__ import annotations

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Data_Validation_Error,
    Exception_External_Service_Error,
    Exception_Serialization_Error,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

# Module-level logger â€” one per module, initialised at import time.
_logger = get_logger(__name__)
```

### Structured logging and context binding

```python
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Data_Validation_Error,
    Exception_External_Service_Error,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def process_client_portfolio_QWIM(
    client_id: str,
    file_path: Path,
) -> pl.DataFrame:
    """Load and validate a single client's portfolio file.

    Parameters
    ----------
    client_id : str
        Unique client identifier used for log context binding.
    file_path : pathlib.Path
        Path to the client's Parquet portfolio file.

    Returns
    -------
    polars.DataFrame
        Validated portfolio frame sorted by ``Date``.

    Raises
    ------
    Exception_Data_Validation_Error
        Raised when the portfolio file is missing required columns.
    Exception_External_Service_Error
        Raised when the file cannot be read (I/O failure).

    Notes
    -----
    Uses ``_logger.bind`` to attach ``client_id`` to all log records
    emitted within this function scope. This is the preferred pattern
    over concatenating the client ID into every message string.
    """
    # Bind client context â€” all subsequent log calls in this scope carry client_id.
    bound_logger = _logger.bind(client_id=client_id)
    bound_logger.info("Starting portfolio load")

    try:
        data_frame = pl.read_parquet(file_path)
    except Exception as exc:
        bound_logger.exception("I/O error reading portfolio file: %s", file_path)
        raise Exception_External_Service_Error(
            "Failed to read portfolio Parquet file.",
            service="filesystem",
            detail={"client_id": client_id, "path": str(file_path)},
        ) from exc

    required_columns = {"Date", "Portfolio_Value"}
    missing_columns = required_columns - set(data_frame.columns)
    if missing_columns:
        raise Exception_Data_Validation_Error(
            "Portfolio file missing required columns.",
            field="columns",
            value=sorted(missing_columns),
        )

    result = data_frame.sort("Date")
    bound_logger.info("Portfolio loaded successfully: %s rows", result.height)
    return result
```

### Retry with tenacity

```python
from __future__ import annotations

from typing import Any

import tenacity

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_External_Service_Error,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),            # maximum 3 attempts
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),  # 1s, 2s, 4s backoff
    retry=tenacity.retry_if_exception_type(Exception_External_Service_Error),
    before_sleep=tenacity.before_sleep_log(_logger, tenacity.logging.WARNING),  # log before each retry
    reraise=True,                                   # re-raise after all attempts exhausted
)
def fetch_market_data_QWIM(
    ticker: str,
    api_client: Any,
) -> dict[str, Any]:
    """Fetch market data with automatic retry on transient failures.

    Parameters
    ----------
    ticker : str
        Security ticker symbol.
    api_client : Any
        Client object with a ``get_price(ticker)`` method.

    Returns
    -------
    dict[str, Any]
        Market data payload returned by the API.

    Raises
    ------
    Exception_External_Service_Error
        Re-raised after all retry attempts are exhausted.

    Notes
    -----
    The ``@tenacity.retry`` decorator handles the retry loop; manual
    ``while`` loops with ``time.sleep`` are explicitly forbidden.
    ``before_sleep`` ensures each retry attempt is logged at WARNING
    level with the attempt number and wait duration.
    """
    try:
        return api_client.get_price(ticker)
    except Exception as exc:
        raise Exception_External_Service_Error(
            f"Market data fetch failed for ticker '{ticker}'.",
            service="market_data_api",
            detail={"ticker": ticker},
        ) from exc
```

### Exception hierarchy reference

| Exception class | When to use |
|---|---|
| `Exception_Data_Validation_Error` | Required columns missing, wrong dtype, schema mismatch |
| `Exception_Validation_Input` | User-facing invalid input (from Shiny UI or API request) |
| `Exception_External_Service_Error` | Third-party API, database, or filesystem failure |
| `Exception_Serialization_Error` | JSON/Parquet encode-decode failure |
| `Exception_Security_Violation` | Path traversal, unauthorized access attempt |
| `Exception_Not_Found` | Expected resource (file, record) does not exist |
| `Exception_Invalid_State` | Internal state machine violation |

### Logger and exception pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| F-string allocated even when log level suppressed | `_logger.info(f"Loaded {n} rows")` | Use `_logger.info("Loaded %s rows", n)` |
| Multiple loggers with same `__name__` | Logger initialised inside a function called repeatedly | Move `_logger = get_logger(__name__)` to module top-level |
| `from loguru import logger` in application code | Direct loguru import bypasses masking and handler setup | Replace with `from ...logger_custom import get_logger` |
| Exception traceback lost on re-raise | `raise Exception_...` without `from exc` | Always use `raise Exception_... from exc` |
| Retry loop with `time.sleep` | Manual retry instead of tenacity | Replace with `@tenacity.retry(...)` decorator |
| Secret appears in structured log | PII not masked before binding | Use logger infrastructure masking helpers before `bind()` |

*See also: Zone 5 (Security) for secret masking patterns; Zone 2 (Testing) for asserting log output.*

---

## Zone 4: Shiny Dashboard Architecture

This zone defines the canonical architecture for building Shiny (Posit/Python) dashboards in the QWIM project. It covers module decomposition into tabs and subtabs, the hierarchical identifier naming convention, reactive programming patterns, input validation with `shiny-validate`, server decomposition, and Posit Connect deployment â€” giving a coding agent everything needed to extend or maintain the dashboard without introducing reactive leaks, identifier collisions, or untestable server logic.

### Zone 4 mandatory rules

1. Every Shiny dashboard is decomposed into one Python file per tab (`tab_<name>.py`) and one file per subtab (`subtab_<name>.py`); no tab logic belongs in `app.py` beyond wiring.
2. Shiny input identifiers follow `input_ID_tab_<tabname>_subtab_<subtabname>_<field>` and output identifiers follow `output_ID_tab_<tabname>_subtab_<subtabname>_<field>`; identifiers without the full hierarchical prefix are forbidden.
3. All heavy computation, validation, and domain logic live in pure Python functions outside reactive blocks; reactive blocks contain only wiring, not arithmetic.
4. Validate all user inputs at the reactive boundary using `shiny-validate`; pass a validated dict to domain functions â€” domain functions must not call `input.<id>()` directly.
5. Store reactive display state in a `dict[str, Any]` named `Reactive_State_<TabName>` (using `reactive.Value({})`) rather than one `reactive.Value` per widget â€” this reduces reactive graph edges and prevents cascade invalidation.
6. Use `@reactive.Calc` (memoised) for derived values shared across multiple output renderers; use `@reactive.Effect` only for side effects with no return value.
7. All Shiny test files use the `test_shiny_` prefix and live under `tests/tests_shiny/` mirroring `src/` structure.
8. Use `render.DataTable` with a `polars.DataFrame` converted to `pandas` only at the render boundary (`data_frame.to_pandas()`); all upstream processing stays in Polars.
9. Never import a subtab module inside a reactive block â€” all imports happen at module top-level.
10. Log all unhandled reactive exceptions through `_logger.exception(...)` before re-raising as `Exception_Validation_Input` so the UI receives a user-friendly error message.

### Canonical tab/subtab decomposition

```python
# File: src/dashboard/tab_portfolios.py
"""Portfolios tab â€” wires subtabs and composes the tab UI.

Notes
-----
This file contains only UI composition and server wiring.
All domain logic lives in ``subtab_portfolios_*.py`` files.
"""
from __future__ import annotations

import shiny.ui as ui
from shiny import module

from src.dashboard.subtab_portfolios_overview import (
    subtab_portfolios_overview_server,
    subtab_portfolios_overview_ui,
)
from src.dashboard.subtab_portfolios_allocation import (
    subtab_portfolios_allocation_server,
    subtab_portfolios_allocation_ui,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def tab_portfolios_ui() -> ui.Tag:
    """Return the Portfolios tab UI component.

    Returns
    -------
    shiny.ui.Tag
        Navset panel containing all portfolio subtabs.
    """
    return ui.nav_panel(
        "Portfolios",
        ui.navset_tab(
            subtab_portfolios_overview_ui("portfolios_overview"),
            subtab_portfolios_allocation_ui("portfolios_allocation"),
        ),
    )


def tab_portfolios_server(
    input,
    output,
    session,
) -> None:
    """Wire the Portfolios tab server modules.

    Parameters
    ----------
    input : shiny.Inputs
        Shiny input object.
    output : shiny.Outputs
        Shiny output object.
    session : shiny.Session
        Current session.

    Returns
    -------
    None
        Side effect: registers reactive computations in the Shiny session.
    """
    subtab_portfolios_overview_server("portfolios_overview", input, output, session)
    subtab_portfolios_allocation_server("portfolios_allocation", input, output, session)
    _logger.debug("Portfolios tab server wired")
```

### Canonical subtab with validation

```python
# File: src/dashboard/subtab_portfolios_allocation.py
"""Portfolio allocation subtab â€” input validation and reactive wiring.

Notes
-----
All domain computation is delegated to pure functions in
``src/portfolios/``. This file contains only reactive wiring and
input-validation logic per the project's clean-boundary rule.
"""
from __future__ import annotations

from decimal import Decimal

import shiny.ui as ui
from shiny import module, reactive, render
from shiny_validate import InputValidator, check

from src.portfolios.calc_allocation import calc_rebalance_plan_QWIM
from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def subtab_portfolios_allocation_ui(
    module_id: str,
) -> ui.Tag:
    """Return the Allocation subtab UI component.

    Parameters
    ----------
    module_id : str
        Shiny module namespace identifier.

    Returns
    -------
    shiny.ui.Tag
        Nav panel containing the allocation input form and result table.
    """
    return ui.nav_panel(
        "Allocation",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_numeric(
                    "input_ID_tab_portfolios_subtab_allocation_target_weight",
                    label="Target weight (%)",
                    value=50,
                    min=0,
                    max=100,
                ),
                ui.input_action_button(
                    "input_ID_tab_portfolios_subtab_allocation_run_btn",
                    "Calculate rebalance",
                    class_="btn-primary",
                ),
            ),
            ui.output_table("output_ID_tab_portfolios_subtab_allocation_plan_table"),
        ),
    )


def subtab_portfolios_allocation_server(
    module_id: str,
    input,
    output,
    session,
) -> None:
    """Wire the Allocation subtab reactive logic.

    Parameters
    ----------
    module_id : str
        Shiny module namespace identifier.
    input : shiny.Inputs
        Shiny input object.
    output : shiny.Outputs
        Shiny output object.
    session : shiny.Session
        Current session.

    Returns
    -------
    None
        Side effect: registers reactive computations.
    """
    # --- Input validation using shiny-validate ---
    validator_allocation = InputValidator()
    validator_allocation.add_rule(
        "input_ID_tab_portfolios_subtab_allocation_target_weight",
        check.required("Target weight is required"),
        check.between(0, 100, "Weight must be between 0 and 100"),
    )
    validator_allocation.enable()

    @reactive.Calc
    def calc_rebalance_plan():
        """Compute rebalancing plan from validated inputs.

        Returns
        -------
        polars.DataFrame | None
            Rebalancing plan frame, or None when inputs are invalid.
        """
        if not validator_allocation.is_valid():
            return None
        target_pct = input.input_ID_tab_portfolios_subtab_allocation_target_weight()
        target_weight = Decimal(str(target_pct)) / Decimal("100")
        try:
            return calc_rebalance_plan_QWIM(target_weight=target_weight)
        except Exception_Validation_Input as exc:
            _logger.warning("Allocation validation failed: %s", exc)
            return None
        except Exception as exc:
            _logger.exception("Unexpected error in allocation calculation")
            raise

    @output
    @render.table
    def output_ID_tab_portfolios_subtab_allocation_plan_table():
        """Render the rebalancing plan table.

        Returns
        -------
        pandas.DataFrame | None
            Pandas frame for Shiny table renderer (pandas boundary at render only).
        """
        plan = calc_rebalance_plan()
        if plan is None:
            return None
        return plan.to_pandas()  # pandas-boundary: Shiny render.table requires pandas
```

### Shiny pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| Reactive loop / infinite invalidation | `reactive.Value` mutated inside `@reactive.Calc` | Never write to a `reactive.Value` inside a `@reactive.Calc`; use `@reactive.Effect` |
| Identifier collision between subtabs | Short IDs without full tab/subtab prefix | Enforce `input_ID_tab_<tab>_subtab_<subtab>_<field>` naming |
| Heavy computation on every keystroke | Domain logic inside `@render.*` block | Move to `@reactive.Calc` so result is memoised |
| `to_pandas()` in domain logic | Premature pandas conversion upstream of render | Move conversion to final `@render.table` block only |
| Missing validation feedback | Input validated only in domain function | Add `shiny-validate` `InputValidator` at the reactive boundary |
| Module import inside reactive block | Import inside `@reactive.Calc` causes re-import on every invalidation | Move imports to module top-level |

*See also: Zone 3 (Logger) for exception handling inside reactive blocks; Zone 5 (Security) for validating file-path inputs from Shiny UI.*

---

## Zone 5: Security and Validation

This zone defines the security and input-validation standards for the QWIM codebase. It covers secret management, path traversal prevention, subprocess security, Pydantic strict models, settings-from-environment patterns, and the layered validation hierarchy â€” ensuring that system boundaries are hardened before domain logic runs.

### Zone 5 mandatory rules

1. Secrets (API keys, passwords, database URLs, private keys) must never appear in source code, configuration files committed to version control, or log output; use `pydantic-settings` with `.env` files that are listed in `.gitignore`.
2. Always validate file paths provided by users or external systems against an `allowed_base` directory using `Path.resolve()` and `Path.is_relative_to()`; raise `Exception_Security_Violation` on path traversal attempts.
3. Never use `subprocess.shell=True` with user-supplied input; always pass arguments as a list to `subprocess.run(..., shell=False)`.
4. Use `secrets.token_urlsafe()` for cryptographic tokens and nonces; never use `random` module for security-sensitive values.
5. Validate all external data (file uploads, API responses, environment variables, CLI arguments) with a Pydantic model at the entry point; downstream functions receive validated typed objects, not raw dicts or strings.
6. Pydantic models used at security boundaries must set `model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)` so unexpected fields and post-construction mutations are rejected.
7. Use `pydantic-settings` `BaseSettings` with `SettingsConfigDict(env_prefix="QWIM_", case_sensitive=False, extra="forbid")` for all environment-driven configuration.
8. Log all security-relevant events (authentication, path validation failures, permission denials) at WARNING level or above; include enough context to diagnose the incident without logging the secret itself.
9. Sanitize inputs before use in file names, SQL queries (if ever introduced), or template rendering; prefer allowlist validation over denylist.
10. Rate-limit external API calls using `tenacity`; document the limit in the docstring `Notes` section.

### Pydantic strict boundary model

```python
"""Pydantic models for secure, strict boundary validation of QWIM inputs.

Notes
-----
All models use ``extra="forbid"`` and ``frozen=True`` so unexpected keys
are rejected at construction and post-construction mutation raises an error.
Field constraints are declared once on ``Field(...)`` â€” never duplicated
inside custom validators.
"""
from __future__ import annotations

import secrets
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Self

from aenum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Security_Violation,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


class Risk_Profile_Type(Enum):
    """Allowed risk profile values.

    Notes
    -----
    Using ``aenum.Enum`` per the project standard; ``pl.Enum`` is the
    Polars-side counterpart for DataFrame columns.
    """

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class Model_Client_Input_QWIM(BaseModel):
    """Strict validated model for client onboarding input.

    Attributes
    ----------
    client_id : str
        Unique client identifier; minimum 3 characters.
    age : int
        Client age in years; must be in [18, 120].
    risk_profile : Risk_Profile_Type
        Client's risk tolerance classification.
    initial_investment : Decimal
        Initial portfolio value; must be positive and at most 100 million.
    target_retirement_date : date
        Target retirement date; must be after today.
    """

    client_id: str = Field(min_length=3, max_length=50)
    age: int = Field(ge=18, le=120)
    risk_profile: Risk_Profile_Type
    initial_investment: Decimal = Field(gt=Decimal("0"), le=Decimal("100_000_000"))
    target_retirement_date: date

    model_config = ConfigDict(
        extra="forbid",           # reject unexpected fields immediately
        validate_assignment=True, # re-validate on attribute assignment
        frozen=True,              # prevent mutation after construction
    )

    @field_validator("client_id")
    @classmethod
    def normalize_client_id_QWIM(
        cls,
        value_id: str,
    ) -> str:
        """Normalize client ID to uppercase stripped string.

        Parameters
        ----------
        value_id : str
            Raw client ID from user input.

        Returns
        -------
        str
            Upper-cased, whitespace-stripped client ID.
        """
        return value_id.strip().upper()

    @model_validator(mode="after")
    def validate_retirement_date_QWIM(
        self,
    ) -> Self:
        """Validate that the retirement date is consistent with age.

        Returns
        -------
        Model_Client_Input_QWIM
            The validated model instance.

        Raises
        ------
        ValueError
            If implied retirement age is below 50 or above 90.
        """
        years_to_retirement = self.target_retirement_date.year - date.today().year
        implied_retirement_age = self.age + years_to_retirement
        if not (50 <= implied_retirement_age <= 90):
            raise ValueError(
                f"Implied retirement age {implied_retirement_age} is outside the allowed range [50, 90]."
            )
        return self


class Settings_QWIM(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes
    ----------
    api_key_market_data : str
        Market data API key; sourced from ``QWIM_API_KEY_MARKET_DATA`` env var.
    database_url : str
        Database connection URL; sourced from ``QWIM_DATABASE_URL`` env var.
    secret_session_key : str
        HMAC session secret; auto-generated if not set in environment.
    """

    api_key_market_data: str  # sourced from QWIM_API_KEY_MARKET_DATA
    database_url: str         # sourced from QWIM_DATABASE_URL
    secret_session_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="QWIM_",
        case_sensitive=False,
        extra="forbid",
    )
```

### Path traversal prevention

```python
from __future__ import annotations

from pathlib import Path

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Security_Violation,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)

# All client data must reside within this base directory.
BASE_DATA_DIR = Path("data/clients").resolve()


def validate_client_file_path_QWIM(
    user_path: str | Path,
    allowed_base: Path = BASE_DATA_DIR,
) -> Path:
    """Validate that a user-provided path is within the allowed directory.

    Prevents path traversal attacks (e.g., ``../../etc/passwd``).

    Parameters
    ----------
    user_path : str or pathlib.Path
        Path provided by the user or external system.
    allowed_base : pathlib.Path, optional
        Absolute base directory; defaults to ``BASE_DATA_DIR``.

    Returns
    -------
    pathlib.Path
        Validated, resolved absolute path.

    Raises
    ------
    Exception_Security_Violation
        Raised when the resolved path escapes ``allowed_base``.

    Notes
    -----
    Uses ``Path.is_relative_to()`` (Python 3.9+) after resolving both
    paths to absolute canonical forms. Symlinks are followed by
    ``Path.resolve()`` so a symlink pointing outside the allowed directory
    is caught correctly.
    """
    resolved_path = (allowed_base / user_path).resolve()
    resolved_base = allowed_base.resolve()

    if not resolved_path.is_relative_to(resolved_base):
        _logger.warning(
            "Path traversal attempt blocked: user_path=%s resolved=%s",
            user_path,
            resolved_path,
        )
        raise Exception_Security_Violation(
            f"Path '{user_path}' resolves outside the allowed directory '{resolved_base}'.",
        )

    return resolved_path
```

### Security pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| Secret appears in log | PII or token logged directly | Mask with logger infrastructure before `bind()` or `info()` |
| Path traversal succeeds | `os.path.join` used without `resolve()` | Use `(base / user_path).resolve()` + `is_relative_to(base)` |
| `subprocess` shell injection | `subprocess.run(cmd, shell=True)` with user input | Pass as list: `subprocess.run([cmd, arg1, arg2], shell=False)` |
| Pydantic ignores extra fields | Model missing `extra="forbid"` | Add `ConfigDict(extra="forbid")` |
| API key in pyproject.toml | Hardcoded secret in config | Move to `.env` + `pydantic-settings` |
| Random token is predictable | Used `random.token_hex()` | Replace with `secrets.token_urlsafe()` |

*See also: Zone 3 (Logger) for masking helpers; Zone 4 (Shiny) for validating file-upload paths.*

---

## Zone 6: Performance Patterns

This zone documents the performance optimisation playbook for the QWIM codebase. It covers `__slots__`, `@dataclass(frozen=True, slots=True)`, `functools.cache`, `lru_cache`, lazy Polars pipelines, generator patterns for large streams, profiling with `cProfile`, and benchmarking â€” giving coding agents a decision tree that prevents premature optimisation while ensuring the most common bottlenecks (Python object overhead, eager Polars materialisation, unbounded caches) are avoided by default.

### Zone 6 mandatory rules

- Profile before optimising: use `cProfile` or `py-spy` to identify the actual bottleneck; never restructure code for performance without profiling data.
- Use `@functools.cache` (unbounded) for pure, deterministic functions that are called with a small finite set of argument combinations (e.g., factor model coefficients for 10 risk profiles); use `@functools.lru_cache(maxsize=128)` when the call space is large or unbounded.
- Keep Polars pipelines lazy until the final `.collect()` call; an intermediate `.collect()` in a chained pipeline forces full materialisation and defeats predicate pushdown.
- Use generators and `itertools` for sequences that are consumed once and are too large to hold in memory; never convert a generator to a list unless the full sequence is required.
- Batch external API and database calls rather than making one call per item in a loop; a single batched request for 1,000 items is typically 10â€“100Ã— faster than 1,000 individual requests.
- Use `numpy` for homogeneous numeric array operations when Polars expressions are not available (e.g., linear algebra, FFT); avoid Python `list` arithmetic on numeric data.
- Pre-compute static lookup tables and schema constants at module import time rather than inside functions that are called repeatedly.
- Use `collect(engine="streaming")` for pipelines whose intermediate results may exceed available RAM; the streaming engine processes data in configurable-size row-group batches.
- Document every optimised function with a `Notes` section that explains why the optimisation was applied and what profiling evidence justified it.

### Cache patterns

```python
from __future__ import annotations

from decimal import Decimal
from functools import cache, lru_cache
from typing import Any

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


@cache  # unbounded â€” suitable only when argument space is small and finite
def calc_discount_factor_QWIM(
    rate_annual: Decimal,
    years: int,
) -> Decimal:
    """Calculate a deterministic discount factor with memoisation.

    Parameters
    ----------
    rate_annual : decimal.Decimal
        Annual discount rate as a decimal fraction (e.g., ``Decimal("0.05")``).
    years : int
        Number of years to discount.

    Returns
    -------
    decimal.Decimal
        Discount factor ``(1 + rate) ** (-years)``.

    Notes
    -----
    ``@cache`` is appropriate here because the QWIM product set uses at most
    ~20 distinct rate/year combinations per run. Profile evidence: without
    caching, this function consumed 12 % of a 60-second scenario run because
    it was called 2 million times with the same 18 arguments.
    """
    return (1 + rate_annual) ** (-years)


@lru_cache(maxsize=256)  # bounded â€” suitable for API responses with large key space
def fetch_risk_factor_QWIM(
    factor_name: str,
    as_of_date: str,  # str because datetime is not hashable without __hash__; use ISO date string
) -> dict[str, Any]:
    """Fetch a risk factor value with LRU-bounded caching.

    Parameters
    ----------
    factor_name : str
        Name of the risk factor (e.g., ``"duration_5y"``).
    as_of_date : str
        ISO date string for the observation date (e.g., ``"2024-01-31"``).

    Returns
    -------
    dict[str, Any]
        Risk factor payload from the data store.

    Notes
    -----
    ``lru_cache`` with ``maxsize=256`` was chosen over ``@cache`` because
    the factor Ã— date key space grows unboundedly over time. The LRU eviction
    policy keeps memory bounded while still serving the ~100 most-recent
    factor queries from cache. Profiling showed a 95 % cache hit rate in
    month-end batch runs.
    """
    _logger.debug("Cache miss for risk factor %s on %s", factor_name, as_of_date)
    # In production, this calls a data store; the mock below illustrates the contract.
    return {"factor": factor_name, "value": 0.0, "as_of_date": as_of_date}
```

### Generator for large portfolio streams

```python
from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path

import polars as pl

from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def iter_client_portfolio_files_QWIM(
    base_dir: Path,
    glob_pattern: str = "*.parquet",
) -> Generator[pl.DataFrame, None, None]:
    """Yield validated portfolio DataFrames one file at a time.

    Parameters
    ----------
    base_dir : pathlib.Path
        Directory containing per-client Parquet portfolio files.
    glob_pattern : str, optional
        Glob pattern for file discovery, by default ``"*.parquet"``.

    Yields
    ------
    polars.DataFrame
        One validated portfolio frame per file, sorted by ``Date``.

    Notes
    -----
    Using a generator avoids loading all client portfolios into memory
    simultaneously. For 50,000 clients at 10 KB each, eager loading would
    require ~500 MB; the generator holds at most one frame at a time.
    Callers that need a combined frame should call
    ``pl.concat(list(iter_client_portfolio_files_QWIM(base_dir)))``
    only when the total fits in available memory.
    """
    for item_path in sorted(base_dir.glob(glob_pattern)):
        try:
            frame = pl.read_parquet(item_path).sort("Date")
            _logger.debug("Yielding portfolio frame from %s (%s rows)", item_path.name, frame.height)
            yield frame
        except Exception as exc:
            _logger.warning("Skipping unreadable portfolio file %s: %s", item_path.name, exc)
```

### Performance pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| Polars pipeline slow despite lazy API | Intermediate `.collect()` inside pipeline | Remove premature `.collect()`; stay lazy until final step |
| Simulation OOM for 1M scenarios | All scenarios loaded into memory with `read_parquet` | Use `scan_parquet` + `collect(engine="streaming")` |
| `@cache` causes memory leak | Unbounded cache on a function with large/infinite key space | Replace with `@lru_cache(maxsize=N)` |
| Python loop 100Ã— slower than expected | `list` arithmetic on numeric data | Delegate to numpy or Polars expression |
| Cold start slow on each request | Static lookup tables computed inside function | Move computation to module top-level constant |
| Profile shows 80% time in one function | Function called NÂ² times with repeated args | Add `@lru_cache` or pre-compute a lookup frame |

*See also: Zone 1 (Polars) for streaming sinks and lazy pipelines; 
---

## Zone 7: Documentation and ProperDocs

This zone defines the documentation standards for the QWIM codebase. It covers Numpydoc docstring structure for every public object, the ProperDocs/mkdocstrings pipeline, strict-build validation, API page organisation, cross-reference patterns, and the prohibition on hand-maintained generated pages â€” ensuring that documentation stays synchronised with code without manual effort.

### Zone 7 mandatory rules

1. Every public module, class, function, and method must have a Numpydoc-style docstring; a public object without a docstring is treated as a documentation coverage gap equivalent to a line-coverage gap.
2. Numpydoc sections appear in this order: summary line, extended description, `Parameters`, `Returns`, `Raises`, `Yields` (if a generator), `Notes`, `Examples`; sections are omitted when not applicable but never reordered.
3. The `Parameters` section lists one entry per parameter in the format `name : type\n    Description.`; the type annotation in the signature and the type in the docstring must be consistent.
4. The `Raises` section documents every exception that can propagate to the caller â€” including those raised by called project functions; undocumented exceptions make the public contract incomplete.
5. The `Examples` section must be executable in principle; snippets use the project's import conventions and `get_logger` rather than `print`.
6. Never edit generated API Markdown pages by hand; all API content is produced by `mkdocstrings[python]` from docstrings â€” hand edits are overwritten on the next `mkdocs build`.
7. Validate the documentation build with `mkdocs build -f properdocs.yml --strict` before committing; a strict-build warning is treated as a blocking error.
8. Use `mkdocs-autorefs` anchors (`[SomeClass.some_method][]`) for cross-references between documented objects; never use hard-coded relative URL strings that break when pages are renamed.
9. Use `mkdocs-gen-files` for programmatically generated summary pages (e.g., module index pages); put the generation script in `docs/gen_ref_pages.py`.
10. Document non-obvious design decisions in a module-level `Notes` section or in a `docs/development/` page; do not rely on commit message history for architecture decisions.

### Canonical Numpydoc docstring template

```python
"""Portfolio rebalancing utilities.

This module provides pure-function implementations of rebalancing
calculations used by the QWIM dashboard's Portfolios tab. All functions
are stateless and side-effect-free to enable straightforward unit testing.

Notes
-----
Functions in this module raise ``Exception_Data_Validation_Error`` for
schema errors and ``Exception_Validation_Input`` for domain-rule violations.
Direct ``loguru`` use is prohibited; all logging routes through
``logger_custom.get_logger``.
"""
from __future__ import annotations

from decimal import Decimal

import polars as pl

from src.utils.custom_exceptions_errors_loggers.exception_custom import (
    Exception_Data_Validation_Error,
    Exception_Validation_Input,
)
from src.utils.custom_exceptions_errors_loggers.logger_custom import get_logger

_logger = get_logger(__name__)


def calc_rebalance_trades_QWIM(
    frame_current: pl.DataFrame,
    frame_target: pl.DataFrame,
    portfolio_value: Decimal,
) -> pl.DataFrame:
    """Calculate the trades required to rebalance a portfolio to target weights.

    Parameters
    ----------
    frame_current : polars.DataFrame
        Current holdings with columns ``Ticker`` (str) and ``Weight_Current``
        (Float64 in [0, 1]).
    frame_target : polars.DataFrame
        Target allocation with columns ``Ticker`` (str) and ``Weight_Target``
        (Float64 in [0, 1]).
    portfolio_value : decimal.Decimal
        Total portfolio market value in dollars; must be positive.

    Returns
    -------
    polars.DataFrame
        Trade blotter with columns ``Ticker``, ``Weight_Change``,
        ``Trade_Value`` (positive = buy, negative = sell), and
        ``Trade_Direction`` (``"buy"`` or ``"sell"`` as ``pl.Enum``).

    Raises
    ------
    Exception_Data_Validation_Error
        Raised when ``frame_current`` or ``frame_target`` is missing
        required columns or contains nulls in weight columns.
    Exception_Validation_Input
        Raised when ``portfolio_value`` is not positive, or when target
        weights do not sum to 1.0 within a tolerance of 1e-6.

    Notes
    -----
    The function is pure: it does not mutate its arguments and has no
    side effects. Callers may safely pass the same frame to multiple
    rebalancing scenarios without defensive copying.

    Trade values are computed as ``(Weight_Target - Weight_Current) * portfolio_value``.
    No transaction costs or liquidity constraints are modelled at this layer.

    Examples
    --------
    >>> import polars as pl
    >>> from decimal import Decimal
    >>> current = pl.DataFrame({"Ticker": ["AAPL", "MSFT"], "Weight_Current": [0.6, 0.4]})
    >>> target = pl.DataFrame({"Ticker": ["AAPL", "MSFT"], "Weight_Target": [0.5, 0.5]})
    >>> result = calc_rebalance_trades_QWIM(current, target, Decimal("100000"))
    >>> # result contains Weight_Change: [-0.1, 0.1] and Trade_Value: [-10000, 10000]
    """
    # Validate schema at function boundary.
    for col_name, frame in [("Weight_Current", frame_current), ("Weight_Target", frame_target)]:
        if col_name not in frame.columns:
            raise Exception_Data_Validation_Error(
                f"Required column '{col_name}' missing from input frame.",
                field="columns",
                value=[col_name],
            )

    if portfolio_value <= 0:
        raise Exception_Validation_Input(
            "Portfolio value must be positive.",
            field="portfolio_value",
            value=str(portfolio_value),
        )

    blotter = (
        frame_current.join(frame_target, on="Ticker", how="inner")
        .with_columns(
            (pl.col("Weight_Target") - pl.col("Weight_Current")).alias("Weight_Change"),
        )
        .with_columns(
            (pl.col("Weight_Change") * float(portfolio_value)).alias("Trade_Value"),
            pl.when(pl.col("Weight_Change") > 0)
            .then(pl.lit("buy"))
            .otherwise(pl.lit("sell"))
            .cast(pl.Enum(["buy", "sell"]))
            .alias("Trade_Direction"),
        )
    )
    _logger.info("Rebalance blotter computed: %s trades", blotter.height)
    return blotter
```

### ProperDocs configuration reference

The strict documentation build is the primary quality gate:

```powershell
# Run the strict build â€” all warnings are errors
.\.venv\Scripts\mkdocs.exe build -f properdocs.yml --strict

# Serve locally for preview (hot-reload on edit)
.\.venv\Scripts\mkdocs.exe serve -f properdocs.yml
```

Key `properdocs.yml` plugin configuration pattern (do not hand-edit generated API pages):

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: numpy        # Numpydoc parsing
            show_source: true             # show source links
            show_root_heading: true
            separate_signature: true
            show_signature_annotations: true
            members_order: source         # preserve source declaration order
  - autorefs: {}                          # enables [SomeClass.method][] cross-refs
  - gen-files:
      scripts:
        - docs/gen_ref_pages.py           # generates API index pages
```

### Documentation pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| `mkdocs build --strict` fails on `WARNING: Cannot resolve` | Cross-reference uses hard-coded URL | Replace with `[ClassName.method][]` autorefs anchor |
| API page missing a function | Function not imported in `__init__.py` | Add to `__all__` and ensure the module is in `docs/gen_ref_pages.py` |
| Docstring type disagrees with annotation | Copy-paste drift | Run `zensical` docstring linter as part of pre-commit |
| `Examples` section uses `print(...)` | `print` forbidden in production-style examples | Replace with `# result â†’ ...` comments or `_logger.info(...)` |
| Hand-edited API Markdown overwritten | Edited a file under `docs/api/` | Never edit generated pages; edit the source docstring |

*See also: Zone 2 (Testing) for `mkdocs-coverage` integration; Zone 8 (Typing) for annotating `Self` and generic return types in docstrings.*

---

## Zone 8: Modern Python 3.12+ Typing

This zone documents the modern type annotation standards for the QWIM codebase. It covers the PEP 695 `type` alias statement, `Self`, `Literal`, `ParamSpec`, `TypeVar` with bounds, `override`, structural pattern matching, `@dataclass(slots=True)`, and the correct `collections.abc` vs `typing` import split â€” giving coding agents a precise contract for writing type-correct code that passes `ty`, `pyright`, and `pyrefly` without suppressions.

### Zone 8 mandatory rules

1. Every module starts with `from __future__ import annotations`; this enables PEP 563 deferred evaluation of annotations so forward references work without quoting and runtime overhead is eliminated.
2. Use the PEP 695 `type` statement for type aliases (`type Portfolio_Weights = dict[str, Decimal]`) rather than the older `Portfolio_Weights = dict[str, Decimal]` assignment form; the `type` statement is generic-capable and communicates intent to both humans and type checkers.
3. Prefer PEP 604 union syntax `int | None` over `Optional[int]`; the pipe syntax is more readable and consistent with Python's `isinstance(x, int | None)` runtime form.
4. Use `Self` (from `typing`) for methods that return `self` or a new instance of the same class; never annotate return type as the class name string.
5. Use `Literal["value1", "value2"]` for parameters constrained to a small set of string values; this gives the type checker the ability to catch invalid literals at analysis time.
6. Use `ParamSpec` and `Concatenate` when writing decorators that wrap functions to preserve the wrapped function's signature in the type system.
7. Use `TypeVar` with `bound=` for generic functions that operate on a hierarchy; never use unconstrained `TypeVar` when a bound or `Protocol` would work.
8. Import abstract base types from `collections.abc` (`Callable`, `Sequence`, `Mapping`, `Iterator`, `Generator`) rather than `typing`; the `typing` equivalents are deprecated aliases.
9. Use `@override` (from `typing`, Python 3.12+) on any method that overrides a base class method; this allows type checkers to detect signature drift after base class refactoring.
10. Use `typing.assert_never` at the bottom of exhaustive `match` / `if-elif` chains to cause a type error when a new enum member is not handled.
11. Type `**kwargs` as `**kwargs: Unpack[TypedDict_T]` when the keyword argument names and types are known; avoid `**kwargs: Any` in public APIs.

### Type-checking tool matrix

| Tool | Command | When to run | Checks |
|---|---|---|---|
| `ty` | `.venv\Scripts\ty.exe check src/` | Pre-commit, CI | Fast inference errors, type narrowing, `Self` correctness |
| `pyright` | `.venv\Scripts\pyright.exe src/` | CI, on-demand | Strict protocol conformance, overload resolution |
| `pyrefly` | `.venv\Scripts\pyrefly.exe check src/` | CI | Additional flow-sensitive checks |
| `ruff` | `.venv\Scripts\ruff.exe check src/` | Pre-commit, CI | Linting, import order, unused imports |

### Typing pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| `Self` causes `TypeError` at runtime | Missing `from __future__ import annotations` | Add to every module top |
| Old alias syntax not generic-capable | `TypeAlias` or plain assignment used | Replace with PEP 695 `type Name = ...` |
| Decorator erases parameter types | `*args: Any, **kwargs: Any` in wrapper | Use `ParamSpec` + `Concatenate` |
| Exhaustive match has runtime fallthrough | No `assert_never` on `case _:` | Add `assert_never(unreachable)` |
| `ty` ignores `@override` | `from typing_extensions import override` used | Use `from typing import override` (Python 3.12+) |
| `collections.abc.Callable` vs `typing.Callable` | `from typing import Callable` in 3.12+ code | Replace with `from collections.abc import Callable` |

*See also: Zone 3 (Logger) for `ParamSpec`-typed decorator wrappers.*

---

## Extended Reference: Cross-Zone Patterns and Decision Guides

This section provides comprehensive cross-zone reference material that an LLM coding agent should consult when making design decisions that span multiple concerns: choosing the right Polars data type for a new column, deciding whether a new class should use `attrs` or `@dataclass` or `msgspec.Struct` or `pydantic.BaseModel`, selecting the minimum necessary exception type from the project hierarchy, picking the correct test category for a new piece of behaviour, and resolving conflicts between competing coding-standard rules. The guidance here is authoritative and supersedes any general Python coding advice that contradicts it.

### Comprehensive Polars data-type and expression decision guide

When adding a new column to a QWIM frame, apply the following rules in order: (1) if the values are a fixed enumeration of strings known at design time (risk profile, asset class, instrument type, rebalancing frequency), use `pl.Enum` — **never** `pl.String` — because `pl.Enum` validates values at insertion time and is dictionary-encoded for O(1) comparison; (2) if the values are a numeric count that is always non-negative and fits in 16 bits, use `pl.UInt16` rather than `pl.Int64` because the smaller type reduces memory footprint by 4× in large frames; (3) if the values represent money with exact rounding requirements (fees, tax amounts, dividends that must be reportable to the cent), use `pl.Decimal` with an explicit precision and scale rather than `pl.Float64`, and document the scale in the schema constant; (4) if the values are produced by a Monte Carlo simulation where rounding is acceptable and the column participates in SIMD-accelerated vector operations, use `pl.Float64`; (5) if the column carries heterogeneous nested data (e.g., a per-instrument property bag with varying keys), use `pl.Struct` with named fields rather than serialising to JSON strings and storing as `pl.String` — the `Struct` type keeps the data in Arrow columnar memory and exposes typed field-access expressions via `.struct.field("field_name")`; (6) if the column is a variable-length list of same-type values (e.g., a list of daily returns for each scenario grouped by client), use `pl.List(pl.Float64)` rather than storing in separate rows with a row-number key, because `pl.List` operations (`.list.mean()`, `.list.std()`, `.list.arg_min()`) are vectorised across rows.

When choosing between a lazy and eager Polars API, apply the following: use `pl.scan_parquet` / `pl.scan_csv` / `.lazy()` for any pipeline with more than two chained transformations, any pipeline that conditionally applies a filter before an expensive join, or any pipeline that ultimately calls `sink_parquet`; use `pl.read_parquet` / `pl.read_csv` (eager) only for single-transformation operations on small frames that must be fully materialised before the function returns a value to a non-Polars caller (e.g., a Pydantic validator that needs to inspect specific values). The key invariant is: **collect at the call-site boundary, not inside library functions** — library functions should accept and return `LazyFrame` when the consumer might want to compose further transformations, and return `DataFrame` only when the data contract specifies a fully-materialised result.

The `pl.Expr.over()` window function is the correct Polars idiom for any calculation that must be computed independently within each group but the result must be aligned back to the original rows (i.e., the frame height is unchanged). It replaces the pandas `groupby + transform` pattern. The expression `pl.col("Return").rolling_std(window_size=20).over("Risk_Profile")` computes a 20-day rolling standard deviation for each `Risk_Profile` group and re-aligns the result to the original row positions, all in a single Polars kernel invocation without any Python-level merge step.

Null handling in Polars is explicit by design: a `null` in a `Float64` column is not the same as `float('nan')`; Polars propagates `null` through arithmetic (the result is `null`) but propagates `NaN` as a numeric value that participates in comparisons. The QWIM convention is to use `null` exclusively and never introduce `NaN` into domain data. When reading external data that uses `NaN` as a sentinel (common in numpy-generated CSVs), add `.with_columns(pl.col(col).fill_nan(None))` immediately after the read step to convert all `NaN` values to `null` before the frame enters any QWIM pipeline. The `is_null()` / `fill_null()` / `drop_nulls()` expressions then work correctly and predictably.

Schema evolution in QWIM pipelines follows a two-phase discipline: the physical read phase accepts any extra columns from the provider by using `schema_overrides` for known columns only, and the logical narrowing phase applies a `.select(list(REQUIRED_SCHEMA))` immediately after validation to discard unknowns. This decoupling means that when a data vendor adds a new field to their feed, the loader does not break — the unknown field passes through the read phase and is silently discarded in the narrowing phase. The only observable change is a new WARNING log record from the validation step listing the extra columns, which alerts the engineering team to update the schema constant if the new column should be promoted to a required field. The reverse scenario — a required column disappearing — is caught by the missing-column check between the two phases, which raises `Exception_Data_Validation_Error` immediately before any computation occurs.

| Polars join type | When to use | Null key behaviour | Sort required? |
|---|---|---|---|
| `join(how="inner")` | Both frames always match on key; unmatched rows should be discarded from both sides | Null keys never match; null rows dropped from both sides | No |
| `join(how="left")` | Every left-frame row must appear in the result; unmatched right rows produce null in right columns | Left null keys appear in output with null right columns | No |
| `join(how="full")` | All rows from both frames must appear; unmatched rows produce null on the opposite side | Null keys on both sides produce separate null-filled rows | No |
| `join_asof(strategy="backward")` | Time-series point-in-time lookup: right key is the latest available value on or before the left key | Rows before the first right key produce null; use `.fill_null()` to supply a default | Both frames must be sorted by join key ascending before calling |
| `join(how="cross")` | Cartesian product for scenario × asset grids or parameter sweep grids | All combinations produced; nulls in either frame propagate | No |
| `join(how="semi")` | Filter left frame to rows that have a matching key in the right frame; right columns are not kept | Null keys in left frame are dropped (null never matches any right key) | No |
| `join(how="anti")` | Filter left frame to rows with **no** matching key in the right frame | Null keys in left frame appear in the output (null never matches, so always retained) | No |

### Complete exception-selection guide

The exception hierarchy in `src/utils/custom_exceptions_errors_loggers/exception_custom.py` is designed so that the most specific exception class is always the correct choice — catching a base class in a `try/except` block will suppress information that is valuable for debugging. Apply the following selection rules: raise `Exception_Data_Validation_Error` when a Polars DataFrame or Series fails a schema check (missing column, wrong dtype, unexpected null, value outside domain), passing `field=` as the column name and `value=` as the list of offending values; raise `Exception_Validation_Input` when a user-facing form field or API parameter fails a business-rule check (retirement age out of range, negative investment amount, end date before start date), passing `field=` as the input identifier and `value=` as the raw user-supplied value; raise `Exception_External_Service_Error` when a third-party API, database query, or filesystem operation fails in a way that is outside the application's control (network timeout, HTTP 5xx, disk I/O error), passing `service=` as the service name and `detail=` as a dict with non-secret context; raise `Exception_Serialization_Error` when a Parquet read, JSON decode, or msgspec decode fails because the byte content is corrupt or version-incompatible; raise `Exception_Security_Violation` when a path traversal attempt is detected, an SSRF check fails, an authentication token is absent, or an access-control rule is violated — always log at WARNING before raising; raise `Exception_Not_Found` when a required file, database record, or configuration key is absent and no default exists; raise `Exception_Invalid_State` when an internal state machine reaches a branch that should be unreachable given correct upstream logic. Never catch a broad `Exception` in application logic except at the topmost error boundary of a Shiny reactive renderer or a CLI entry point, where the purpose is to sanitise the error message before displaying it to the user.

| Exception class | `field` arg | `value` arg | `service` arg | When NOT to use |
|---|---|---|---|---|
| `Exception_Data_Validation_Error` | Column name or schema field | Offending value or list | N/A | Not for user input errors; not for I/O failures |
| `Exception_Validation_Input` | Form field ID or parameter name | Raw user-supplied value | N/A | Not for schema errors; not for system errors |
| `Exception_External_Service_Error` | N/A | N/A | Service name | Not for validation; not for security events |
| `Exception_Security_Violation` | N/A | N/A | N/A | Not for validation; not for missing data |
| `Exception_Serialization_Error` | Format identifier | Byte offset or key | N/A | Not for network errors; not for validation |
| `Exception_Not_Found` | Resource identifier | N/A | N/A | Not when a default exists; not for schema errors |
| `Exception_Invalid_State` | State field name | Current state value | N/A | Not for user input; not for external failures |

### Test category selection guide

Selecting the wrong test category is the most common mistake when extending the QWIM test suite. The decision rule is: a **unit test** exercises exactly one function or method in isolation, with all dependencies either injected as fixtures or absent — it never touches the filesystem except through `tmp_path`, never makes network calls, and never imports more than one QWIM module at a time; a **unit test that imports two modules** is almost certainly an **integration test** in disguise and should be moved to `tests/tests_integration/`. An **integration test** exercises the interaction between two or more QWIM modules using real file I/O (Parquet fixtures written in session-scoped conftest), real Polars execution, and real exception propagation without any mocks of QWIM internals; an integration test may mock external APIs or databases. A **regression test** captures the exact numeric output of a pipeline at a known-good state and stores it as a Parquet baseline; regression tests are appropriate for any function whose output is a function of a non-trivial algorithm (e.g., risk-parity weights, rolling volatility) where numerical drift would be undetected by assertion-based tests. A **Hypothesis test** is appropriate whenever the function's correctness is expressible as a property that must hold for all valid inputs (e.g., "portfolio weights always sum to 1.0 for any valid input", "the rebalancing blotter contains only buy or sell directions, never both for the same ticker"). A **Shiny test** uses `shiny.testing.AppDriver` and is appropriate for any subtab where the reactive wiring and input-validation feedback must be exercised through the Shiny event loop — unit tests cannot verify reactive invalidation ordering. A **behave test** is appropriate for acceptance criteria expressed as "Given/When/Then" user scenarios in business language, typically written by or with the product owner. A **Robot Framework test** is appropriate for end-to-end workflow verification that spans the full application stack (file loading → computation → dashboard rendering).

| Test category | File prefix | Location | Mocks QWIM internals? | Uses real filesystem? | Assertion style |
|---|---|---|---|---|---|
| Unit | `test_unit_` | `tests/tests_unit/` | No | `tmp_path` only | `assert_frame_equal`, `pytest.raises`, `pytest.approx` |
| Integration | `test_integration_` | `tests/tests_integration/` | No | Session-scoped Parquet fixtures | `assert_frame_equal`, value spot-checks |
| Regression | `test_regression_` | `tests/tests_regression/` | No | Parquet baseline files | `assert_frame_equal(rtol=1e-6)` against stored baseline |
| Hypothesis | `test_unit_` (same file) | Same as unit tests | No | `tmp_path` only | Property invariant assertions |
| Shiny | `test_shiny_` | `tests/tests_shiny/` | External APIs only | No | `AppDriver.expect_text`, output dimensions |
| Behave | Feature file + step file | `tests/tests_behave/` | External APIs only | `tmp_path` equivalent | Gherkin `Then` assertions |
| Robot Framework | `test_robot_fmk_` | `tests/tests_robot_framework/` | No | Full stack | Keyword-based assertions |

### Shiny reactive design decision guide

The most consequential Shiny architecture decisions are: (1) how many `reactive.Value` instances to use per subtab; (2) whether to use `@reactive.Calc` or `@reactive.Effect` for a given computation; (3) how to scope `InputValidator` instances relative to the reactive graph. The QWIM rules are: one `reactive.Value` per subtab holding a `msgspec.Struct` (or frozen Pydantic model) that captures all mutable state, rather than one `reactive.Value` per widget, because a single consolidated state object reduces reactive graph edges from O(n_widgets²) to O(n_widgets); use `@reactive.Calc` for any derived value that is consumed by more than one output renderer or more than one `@reactive.Effect`, because `@reactive.Calc` is memoised and will not recompute unless its dependencies change; use `@reactive.Effect` only for true side effects (writing to a file, sending a notification, mutating a `reactive.Value` from an action-button callback) — never use `@reactive.Effect` when the purpose is to produce a value for rendering; scope one `InputValidator` per subtab (not per widget), call `.add_rule()` for every input widget in the subtab, and call `.enable()` once at subtab server initialisation. The `is_valid()` method of the validator is a reactive endpoint and triggers re-computation of any `@reactive.Calc` that calls it when any input changes.

The Shiny UI component naming convention — `input_ID_tab_<tab>_subtab_<subtab>_<widget_purpose>` — is enforced throughout the codebase. Deviating from this convention breaks the `AppDriver` tests because those tests reference input IDs by their exact string, and any inconsistency between the UI function definition and the test string causes a silent test failure where the driver sets an input that the server never receives. When adding a new input widget, the full five-part ID must be constructed before writing either the UI component or the test that exercises it.

The `@module.ui` / `@module.server` decorator pattern must be used for any subtab that contains more than two output renderers or more than three input widgets, because module scoping prevents namespace collisions between subtabs that have inputs with the same logical purpose (e.g., two subtabs both having a `start_date` input would collide without module scoping). The module namespace prefix is passed automatically to all `input` and `output` accessors within the `@module.server` function, so no manual prefixing is needed inside the module body — only outside it at the parent server's call site.

### Security layered-defence checklist

The QWIM security model is defence-in-depth: each layer catches a different attack surface, and no layer is assumed to be complete without the others. Layer 1 (entry validation): every external input (Shiny UI, CLI argument, API request, file upload) is validated by a Pydantic `BaseModel` with `extra="forbid"` and all field constraints declared via `Field(...)` — this layer catches malformed, unexpected, and out-of-range inputs before they enter domain logic. Layer 2 (path validation): every file path that originates from user input or an external system is validated by `validate_client_file_path_QWIM` against a `BASE_DATA_DIR.resolve()` allowlist using `Path.is_relative_to()` — this layer catches path traversal attacks. Layer 3 (secret management): all secrets are loaded from environment variables via `pydantic-settings` `BaseSettings`; no secret ever appears in source code, log output, or error messages — the `secret_session_key` field in `Settings_QWIM` auto-generates a `secrets.token_urlsafe(32)` value if absent from the environment, so the application fails closed (uses a random ephemeral key) rather than open. Layer 4 (output sanitisation): all exceptions caught at Shiny render boundaries are sanitised by `sanitise_exception_for_ui_QWIM` before the message is displayed to the user — only exceptions whose class name appears in `_USER_SAFE_EXCEPTION_TYPES` have their `str(exc)` forwarded; all others receive a generic fallback. Layer 5 (audit logging): all data access, trade execution, and risk-limit override operations emit a structured audit log record via the `"audit"` logger with `correlation_id`, `actor_id`, `operation`, `resource`, and `outcome` fields, written to an append-only audit log sink separate from the operational log.

| Security layer | Mechanism | Exception raised on violation | Log level |
|---|---|---|---|
| Entry validation | Pydantic `BaseModel(extra="forbid")` | `ValidationError` (Pydantic) | WARNING before raising domain exception |
| Path validation | `Path.resolve().is_relative_to(base)` | `Exception_Security_Violation` | WARNING |
| Secret management | `pydantic-settings` from environment | N/A (configuration error at startup) | ERROR at startup |
| Output sanitisation | `sanitise_exception_for_ui_QWIM` | N/A (returns safe string) | EXCEPTION (full traceback) |
| Audit logging | `_audit_logger.bind(...)` | N/A (logging-only) | INFO (success), WARNING (failure) |
| SSRF prevention | `validate_market_data_url_QWIM` | `Exception_Security_Violation` | WARNING |
| Subprocess safety | `subprocess.run([cmd, args], shell=False)` | N/A (prevents shell injection) | N/A |

### Numpydoc section reference and ProperDocs compliance

Every public module, class, function, method, and property in the QWIM codebase must have a complete Numpydoc docstring. The section ordering, formatting rules, and content requirements are as follows: the **summary line** is a single imperative sentence (e.g., "Calculate the rebalancing trades required to reach target weights.") not exceeding 79 characters, followed by a blank line; the **extended description** provides the full context, algorithm overview, assumptions, and any caller obligations that are not captured in the parameter descriptions — it is one or more paragraphs separated by blank lines; the **Parameters** section uses `name : type` format where `type` is the human-readable Python type (e.g., `polars.DataFrame`, `decimal.Decimal`, `pathlib.Path`), not the type annotation syntax — each parameter description explains what the value represents in the QWIM domain, valid ranges, and defaults; the **Returns** section has the same format as Parameters; the **Raises** section lists every exception that can propagate to the caller, including those raised by called project functions; the **Notes** section contains implementation rationale, profiling evidence, invariants, thread-safety notes, and `# numpy-boundary` or `# pandas-boundary` documentation; the **Examples** section contains executable code snippets with QWIM import conventions and `_logger.info(...)` instead of `print(...)`.

The `mkdocs build -f properdocs.yml --strict` command treats every WARNING as a build error. The most common warning types and their resolutions: `WARNING: Cannot resolve 'SomeClass.some_method'` — replace with mkdocs-autorefs anchor `[SomeClass.some_method][]`; `WARNING: Docstring contains no documentation for parameter 'xyz'` — add a `Parameters` entry for `xyz` in the Numpydoc docstring; `WARNING: No module named 'src.some_module'` — add the module to `docs/gen_ref_pages.py`'s discovery path; `WARNING: mkdocstrings could not find object 'src.some_module.SomeClass'` — verify the module is in `__all__` or directly importable, and that `mkdocstrings` `python` handler's `paths` includes `src/`; `WARNING: Duplicate anchor` — use fully-qualified `[module.function][]` anchor syntax instead of bare `[function][]`.

The `properdocs.yml` configuration must include these `mkdocstrings` options: `docstring_style: numpy` (enables Numpydoc parsing), `show_source: true` (adds source links), `separate_signature: true` (renders signature separately for readability), `show_signature_annotations: true` (shows type annotations), `members_order: source` (preserves declaration order), `show_root_heading: true` (adds module/class heading), `docstring_options.ignore_init_summary: false` (renders `__init__` docstrings), and `filters: ["!^_"]` (excludes private members).

| Numpydoc section | Required for | Content rule |
|---|---|---|
| Summary line | All public objects | Single imperative sentence ≤79 chars; no trailing period ambiguity |
| Extended description | Any non-trivial function | Context, algorithm, assumptions, caller obligations — full prose paragraphs |
| Parameters | All functions/methods with parameters | `name : type\n    Description with domain context, valid range, default value` |
| Returns | All non-`None`-returning functions | Describe what the value represents in QWIM terms, not just the Python type |
| Raises | Any function raising or propagating a project exception | Every exception that reaches the caller, with plain-language trigger condition |
| Notes | Any function with non-obvious implementation | Rationale, profiling evidence, invariants, numpy/pandas boundary markers |
| Examples | All public API functions | Executable; QWIM imports; `_logger.info(...)` never `print()` |

### msgspec integration patterns for QWIM data contracts

`msgspec` is the project's preferred library for high-performance serialisation of structured data at internal service boundaries. The key `msgspec.Struct` design rules are: (1) use `frozen=True` for all structs that represent immutable data (configuration, validated inputs, simulation parameters) to get `__hash__` for free and enable use in `functools.cache` key tuples; (2) use `gc=False` for structs instantiated in large numbers (>100,000 per batch run) because `gc=False` removes the struct from Python's garbage-collector tracking, eliminating per-instance GC overhead; (3) declare field types with `Annotated[int, msgspec.Meta(ge=0, le=120)]` and other `msgspec.Meta` constraints — `msgspec` enforces these constraints at decode time without separate validation; (4) use `msgspec.json.encode` / `msgspec.json.decode` for JSON, and `msgspec.msgpack.encode` / `msgspec.msgpack.decode` for binary — both are 10–50× faster than `json.dumps` + Pydantic parse; (5) prefer `msgspec.Struct` over `@dataclass` for objects that cross process boundaries (serialised to a queue, stored in a cache, sent over a websocket) — use `@dataclass` for in-process domain objects that do not need serialisation.

| Serialisation need | Recommended tool | Reason | When NOT to use |
|---|---|---|---|
| Validated user input from Shiny UI or API | `pydantic.BaseModel` | Full validation, Shiny-validate integration, `extra="forbid"` | Not for high-volume internal serialisation (too slow) |
| Internal service boundary (worker queue, cache) | `msgspec.Struct` | 10–50× faster encode/decode; schema constraints at decode | Not for user-facing input (no custom validator methods) |
| Application settings from environment | `pydantic-settings.BaseSettings` | Environment variable loading, `.env` file parsing, secret masking | Not for data objects; not for serialisation |
| In-process immutable domain objects | `@dataclass(frozen=True, slots=True)` | Memory-efficient, `__hash__` from frozen, no serialisation overhead | Not for objects that cross process boundaries |
| Reactive display state in Shiny subtab | `msgspec.Struct(frozen=True)` | Immutable, hashable, fast encode, minimal GC overhead | Not for validation of user input |
| High-throughput binary inter-process messages | `msgspec.Struct` + `msgspec.msgpack` | Smallest message size, fastest decode, schema evolution via `Optional` | Not when human-readable format is needed for debugging |

### Comprehensive naming convention summary

The QWIM naming conventions exist to make code self-documenting across a large multi-contributor codebase where the same concept (a portfolio, a client, a return series) appears in many contexts. The rules apply uniformly to all new code and must not be violated: use `snake_case_with_underscores` for all variable and function names, with the generalisation-to-specialisation ordering (e.g., `estimator_distribution_univariate_lognormal` not `lognormal_estimator`); use `CamelCase_with_underscores` for all class names (e.g., `Portfolio_Builder_QWIM`, `Exception_Data_Validation_Error`); use `UPPERCASE_with_underscores` for all module-level constants and `aenum` enum members (e.g., `SCHEMA_PORTFOLIO_TS`, `RISK_PROFILE_CONSERVATIVE`); use `m_` prefix for instance attributes on classes to distinguish them from local variables and parameters (e.g., `self.m_weights`, `self.m_name`, `self.m_risk_level`); use the `_QWIM` suffix on all public functions and classes that are part of the project API surface (e.g., `load_portfolio_time_series_QWIM`, `Model_Client_Input_QWIM`) — this suffix distinguishes project-specific implementations from imported library symbols in code search and grep results; use the `idx_` or `item_` prefix for loop variables (e.g., `for idx_row in range(n):`, `for item_ticker in tickers:`) — bare single-letter loop variables are forbidden; use `Test_` prefix for test function names and `Class_Test_` prefix for test class names with full `Subject_Condition_Outcome` detail; use file name prefixes (`test_unit_`, `test_integration_`, `test_regression_`, `test_shiny_`, `test_behave_`, `test_robot_fmk_`) to allow test runners to discover and categorise tests by prefix pattern; acronyms in names are always fully uppercase (e.g., `QWIM`, `CAGR`, `SPIA`, `JSON`, `CSV`) even when they appear mid-name (e.g., `format_as_JSON`, `load_CSV_portfolio_QWIM`).

### End-to-end coding checklist for coding agents

When a coding agent (GitHub Copilot, Claude Code, or any LLM-based assistant) creates or modifies Python files in this repository, the following checklist must be satisfied before the change is considered complete: (1) every new or modified Python file starts with `from __future__ import annotations` as the first non-comment, non-docstring line; (2) every new public function, class, and method has a complete Numpydoc docstring with at minimum a summary line, Parameters, Returns, and Raises sections; (3) all logging uses `_logger = get_logger(__name__)` at module level and `_logger.info/warning/error/exception(...)` with `%s`-style lazy formatting — no `f-string` inside log calls, no `print()` anywhere; (4) all exceptions raised are project hierarchy exceptions from `exception_custom.py` — no bare `raise ValueError(...)` or `raise RuntimeError(...)` in domain code; (5) all tabular data is in Polars — no `import pandas` in domain logic; (6) all new Pydantic `BaseModel` classes use `ConfigDict(extra="forbid")` and `frozen=True` where immutability is appropriate; (7) all new test functions follow the `Test_Subject_Condition_Outcome` naming pattern and the AAA structure; (8) all new test files are in the correct `tests/tests_<category>/` subdirectory mirroring the `src/` structure; (9) `mkdocs build -f properdocs.yml --strict` passes without warnings after docstring changes; (10) `ruff check src/` and `ty check src/` pass without new errors after code changes.

---

## Zone 9: Concurrency and Parallelism

This zone defines the allowed concurrency patterns for QWIM workloads that need to balance numerical performance, deterministic behavior, cross-platform compatibility, and safe interaction with Shiny reactivity. Concurrency is not a default design choice. Apply it only when profiling shows that wall-clock performance is limited by an isolated hot path and the added scheduling complexity does not weaken correctness, reproducibility, or deployment safety.

### Zone 9 mandatory rules

1. Profile first. Do not add threads, processes, or executor orchestration without a measured hotspot and a documented reason for the concurrency boundary.
2. Prefer vectorized Polars expressions before Python-level concurrency. A single fused Polars pipeline usually outperforms hand-written threading around row or group loops.
3. Treat Polars as already parallel by default. Avoid wrapping Polars-heavy functions inside a high-worker-count `ThreadPoolExecutor` or `ProcessPoolExecutor` unless profiling shows a clear benefit.
4. For CPU-bound pure Python or numpy-heavy workloads that do not release the GIL, prefer `ProcessPoolExecutor` or `multiprocessing` with an explicit process model.
5. For I/O-bound workloads, such as reading many files, Typst subprocess coordination, or network access, prefer `ThreadPoolExecutor` with bounded worker counts.
6. On Windows, assume the `spawn` process model. Any function dispatched to a process pool must be defined at module scope, must be importable, and must not capture unpicklable closures.
7. On Linux deployment targets, do not assume that `fork` semantics are safe for code that holds open file handles, reactive state, locks, or third-party runtime state. Write code that remains correct under `spawn`.
8. Never mutate Shiny `reactive.Value` objects, shared caches, or caller-owned Polars frames from worker threads or worker processes.
9. Restrict concurrent work to pure, serializable input-output helpers. Marshal data at the boundary and merge results deterministically in the caller.
10. Bound worker counts explicitly. Do not rely on unbounded defaults in environments where Posit Connect may already multiplex multiple sessions.
11. If a function may run inside both a local Windows workstation and a Linux Posit Connect container, document the concurrency assumptions in a `Notes` section and include fallback serial behavior.
12. If failure of a worker leaves partial results on disk, implement cleanup in the parent boundary and document the recovery strategy.

### Executor-selection decision table

| Workload shape | Preferred primitive | Why | Avoid |
|---|---|---|---|
| Single Polars pipeline over large tabular data | Polars lazy execution only | Polars already parallelizes internally | Extra Python threads around `collect()` |
| CPU-bound pure function over many independent scenarios | `ProcessPoolExecutor` | Bypasses GIL and isolates worker state | `ThreadPoolExecutor` if the function is Python-bound |
| Many short-lived file reads or report renders | `ThreadPoolExecutor` with small bounded pool | I/O overlaps well; simple lifecycle | Large process pools |
| Long-running background calculation inside Shiny | Explicit background service boundary | Keeps reactive shell small and testable | Mutating reactive state in a worker |
| Mixed CPU and Polars work | Profile first; often split into serial Polars stage then small process pool | Prevents oversubscription | Parallelizing every stage blindly |

### Parallel Monte Carlo pattern

```python
from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from os import cpu_count


def _calc_path_statistic_QWIM(
    path_seed: int,
) -> float:
    """Calculate a deterministic statistic for one simulation path.

    Parameters
    ----------
    path_seed : int
        Seed used to initialize the path-specific random generator.

    Returns
    -------
    float
        Deterministic summary statistic for the requested path.

    Notes
    -----
    This helper is defined at module scope so it can be serialized under the
    Windows ``spawn`` process model.
    """
    return float(path_seed) / 10.0


def calc_simulation_batch_parallel_QWIM(
    path_seed_vector: Sequence[int],
) -> list[float]:
    """Run independent simulation paths in a bounded process pool.

    Parameters
    ----------
    path_seed_vector : Sequence[int]
        Ordered collection of deterministic path seeds.

    Returns
    -------
    list[float]
        Path statistics in the same order as the input seeds.

    Notes
    -----
    This pattern is appropriate only when profiling shows that a serial
    implementation is the active bottleneck and the worker function is pure.
    The bounded worker count avoids oversubscription on shared deployment
    targets such as Posit Connect.
    """
    worker_count = max(1, min(4, (cpu_count() or 1) - 1))
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(_calc_path_statistic_QWIM, path_seed_vector))
```

### Shiny-safe concurrency boundary

Keep the reactive shell thin. Extract the expensive computation into a pure helper and let the reactive shell only validate inputs, call the helper, and assign the final immutable result back to a `reactive.Value`. If background execution is needed, treat the executor result as an external input and merge it in one place rather than sharing mutable objects across the reactive graph.

### Oversubscription checklist

- Count the number of QWIM sessions that may run simultaneously on Posit Connect.
- Count the internal threads used by Polars and any linked numerical libraries.
- Bound executor workers to leave headroom for the host and other sessions.
- Prefer serial fallback when the input size is small.
- Document the chosen worker count and its rationale in the function docstring.

---

## Zone 10: Cross-Platform Windows, Linux, and Posit Connect

This zone defines the portability rules for QWIM code that must run consistently on a Windows 11 workstation and on a Linux deployment target managed through Posit Connect. The required mindset is portability by construction: use path abstractions, explicit encodings, deterministic subprocess invocation, and environment-driven configuration so the same code path remains valid across both operating systems.

### Zone 10 mandatory rules

1. Use `pathlib.Path` for all filesystem paths. Do not hardcode path separators or platform-specific string manipulations.
2. Open text files with explicit UTF-8 encoding unless a documented external format requires a different encoding.
3. Normalize all user-provided or config-provided paths through `.expanduser()` and `.resolve()` before use.
4. Build subprocess commands as lists and run them with `shell=False`.
5. Never assume the current working directory. Resolve project-relative paths from an explicit base path.
6. Treat environment variables, not local machine paths, as the source of deployment configuration.
7. Use `tempfile` or an explicit configurable temp directory for temporary artifacts; do not write to ad hoc OS-specific temp locations.
8. Document any platform-divergent fallback branch and mark it `# pragma: no cover` only when realistic automated coverage would require an unreasonable environment scaffold.
9. When a path will be surfaced in the UI or logs, preserve the original user intent separately from the resolved internal path.
10. Assume the Posit Connect runtime may have a stricter file-permission model and fewer ambient executables than a developer workstation.
11. Do not assume that fonts, Typst packages, or external binaries present on Windows will exist on Linux unless they are explicitly provisioned.
12. Keep line-ending handling transparent by using text mode and avoiding manual `\r\n` management.

### Platform-difference table

| Concern | Windows 11 workstation | Linux / Posit Connect | QWIM rule |
|---|---|---|---|
| Path separator | `\\` accepted by shell and APIs | `/` | Always use `Path` |
| Process model | `spawn` is standard | `fork` may exist but must not be assumed | Write code that works under `spawn` |
| Case sensitivity | Commonly case-insensitive filesystem | Commonly case-sensitive filesystem | Match exact file names |
| Executable discovery | PATH may include local tools | Container PATH may be minimal | Resolve and validate executable path explicitly |
| Temp storage | User profile temp dirs | Sandboxed service temp dirs | Use configured or managed temp dirs |
| Fonts/assets | Often many local fonts | Deployment image may be sparse | Package or validate required assets |

### Path-validation pattern

```python
from __future__ import annotations

from pathlib import Path


def resolve_output_directory_QWIM(
    output_directory_raw: str | Path,
    project_root_path: Path,
) -> Path:
    """Resolve a report-output directory in a cross-platform-safe way.

    Parameters
    ----------
    output_directory_raw : str | pathlib.Path
        Raw directory supplied by configuration or user input.
    project_root_path : pathlib.Path
        Root path used to resolve relative destinations.

    Returns
    -------
    pathlib.Path
        Absolute normalized output directory path.

    Notes
    -----
    Relative paths are resolved against the explicit project root rather than
    the process working directory so the behavior remains stable on Windows and
    Linux deployment targets.
    """
    output_directory_path = Path(output_directory_raw).expanduser()
    if not output_directory_path.is_absolute():
        output_directory_path = project_root_path / output_directory_path
    return output_directory_path.resolve()
```

### Posit Connect deployment rules

- Treat application startup as non-interactive and non-shell-driven.
- Keep configuration in environment variables or validated settings models.
- Fail fast when a required binary, asset directory, or writable output location is absent.
- Separate user-visible errors from operator-visible logs.
- Do not rely on developer-only cache locations, mapped drives, or GUI-installed software.

### Cross-platform testing guidance

For code with explicit OS-dependent branches, prefer a pure helper that accepts a narrow runtime descriptor rather than calling `platform.system()` deep inside business logic. Test the helper directly. Reserve platform-detection branches for thin boundary code.

---

## Zone 11: Typst and PDF Reporting

This zone defines the reporting and PDF-generation standards for QWIM workflows that compile Typst inputs into deterministic report artifacts. Report generation is treated as a boundary concern: upstream logic prepares validated data and assets, the reporting layer stages those inputs for Typst, and the boundary then invokes Typst with explicit paths, structured logging, and predictable failure semantics.

### Zone 11 mandatory rules

1. Keep data preparation separate from Typst invocation. Pure formatting helpers should not spawn subprocesses.
2. Resolve the Typst executable explicitly and fail with a project exception when it cannot be found.
3. Invoke Typst with `subprocess.run([...], shell=False, check=False)` and inspect the result object directly.
4. Pass absolute input and output paths to Typst.
5. Stage report assets in a dedicated working directory so the rendered output is reproducible and easy to clean up.
6. Log the command intent, input file, output file, and elapsed time, but never log secrets or large embedded payloads.
7. If Typst returns a non-zero exit code, raise a project exception that preserves stderr context for logs and sanitizes any user-facing surface.
8. Keep template selection declarative. Map report type to template path through validated configuration rather than string concatenation in business logic.
9. Use regression tests to compare stable intermediate artifacts or extracted PDF metadata when byte-for-byte PDF equality is too brittle.
10. If external assets such as fonts or images are required, validate their existence before invoking Typst.
11. Prefer deterministic ordering of tables, charts, and context blocks before rendering.
12. Keep subprocess boundaries thin enough that unit tests can validate command construction without launching Typst.

### Report-generation layering

| Layer | Responsibility | Test type |
|---|---|---|
| Pure formatting helper | Build report context from validated inputs | Unit + hypothesis |
| Template resolver | Select template and asset paths | Unit |
| Command builder | Construct Typst subprocess command | Unit + integration |
| Render boundary | Invoke Typst and translate failures | Integration + regression |
| Dashboard/report workflow | Connect UI action to final artifact | Shiny, behave, Robot Framework |

### Typst command-construction pattern

```python
from __future__ import annotations

from pathlib import Path


def build_typst_command_QWIM(
    typst_executable_path: Path,
    input_document_path: Path,
    output_pdf_path: Path,
) -> list[str]:
    """Build a deterministic Typst command.

    Parameters
    ----------
    typst_executable_path : pathlib.Path
        Absolute path to the Typst executable.
    input_document_path : pathlib.Path
        Absolute path to the staged Typst source file.
    output_pdf_path : pathlib.Path
        Absolute path where the PDF should be written.

    Returns
    -------
    list[str]
        Command vector passed directly to ``subprocess.run``.

    Notes
    -----
    The command is constructed as a list so it can be executed with
    ``shell=False`` on both Windows and Linux.
    """
    return [
        str(typst_executable_path),
        "compile",
        str(input_document_path),
        str(output_pdf_path),
    ]
```

### Reporting regression strategy

When PDF bytes are stable enough, store a golden artifact checksum and compare it in regression tests. When full PDF bytes are too brittle because of embedded timestamps or metadata, compare one or more of the following instead:

- normalized Typst input payloads
- extracted document metadata
- page-count expectations
- deterministic table content staged before rendering
- rendered image hashes for a small approved snapshot set

### Reporting failure-handling checklist

- Validate the Typst executable path before command construction
- Validate input template and asset paths before subprocess launch
- Capture stdout and stderr for diagnostics
- Raise a project exception with structured context when compilation fails
- Remove partial temporary artifacts when the render fails after staging