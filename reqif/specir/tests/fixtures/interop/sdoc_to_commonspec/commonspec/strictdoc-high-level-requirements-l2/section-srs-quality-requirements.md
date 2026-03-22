## SECTION-SRS-Quality-requirements @SECTION-SRS-Quality-requirements

> ReqIF.ChapterName: Development process requirements

### SECTION-d36ae155-8261-438a-8221-2f7e41c17725 @SECTION-022

> ReqIF.ChapterName: General process

#### REQUIREMENT: Priority handling of critical issues in StrictDoc @SDOC-SRS-133

> STATUS: Active

> RATIONALE: Prioritizing major issues ensures StrictDoc remains stable and reliable, preventing serious problems that could compromise its performance and integrity.

All critical issues reported in relation to StrictDoc shall be addressed with utmost priority.

### SECTION-SRS-Requirements-engineering @SECTION-SRS-Requirements-engineering

> ReqIF.ChapterName: Requirements engineering

#### REQUIREMENT: Requirements-based development @SDOC-SRS-128

> STATUS: Active

StrictDoc\'s development shall be requirements-based.

#### REQUIREMENT: Self-hosted requirements @SDOC-SRS-91

> STATUS: Active

StrictDoc\'s requirements shall be written using StrictDoc.

### SECTION-SRS-Implementation-requirements @SECTION-SRS-Implementation-requirements

> ReqIF.ChapterName: Implementation requirements

#### SECTION-SRS-Programming-languages @SECTION-SRS-Programming-languages

> ReqIF.ChapterName: Programming languages

##### REQUIREMENT: Python language @SDOC-SRS-8

> STATUS: Active

> RATIONALE: Python has an excellent package ecosystem. It is a widely used language. It is most often the next language for C/C++ programming community when it comes to the tools development and scripting tasks.

StrictDoc shall be written in Python.

#### SECTION-SRS-Cross-platform-availability @SECTION-SRS-Cross-platform-availability

> ReqIF.ChapterName: Cross-platform availability

##### REQUIREMENT: Linux @SDOC-SRS-9

> STATUS: Active

StrictDoc shall support the Linux operating systems.

##### REQUIREMENT: macOS @SDOC-SRS-10

> STATUS: Active

StrictDoc shall support the macOS operating system.

##### REQUIREMENT: Windows @SDOC-SRS-11

> STATUS: Active

StrictDoc shall support the Windows operating system.

### SECTION-SRS-Implementation-constraints @SECTION-SRS-Implementation-constraints

> ReqIF.ChapterName: Implementation constraints

#### REQUIREMENT: Use of open source components @SDOC-SRS-89

> STATUS: Active

> RATIONALE: No commercial/proprietary dependency chain ensures that StrictDoc remain free and open for everyone.

StrictDoc shall be built using only open source software components.

#### REQUIREMENT: No heavy UI frameworks @SDOC-SRS-14

> STATUS: Active

StrictDoc shall avoid using large and demanding UI frameworks. NOTE: An example of frameworks that require a very specific architecture: React JS, AngularJS.

#### REQUIREMENT: No use of NPM @SDOC-SRS-15

> STATUS: Active

> RATIONALE: StrictDoc already deals with the Python/Pip/Pypi ecosystem. The amount of necessary maintenance is already quite high. NPM is known for splitting its projects into very small parts, which increases the complexity of maintaining all dependencies.

StrictDoc shall avoid extending its infrastructure with anything based on NPM-ecosystem.

#### REQUIREMENT: No use of JavaScript replacement languages (e.g., Typescript) @SDOC-SRS-16

> STATUS: Active

> RATIONALE: The development team does not have specific experience with any of the JS alternatives. Staying with a general subset of JavaScript is a safer choice.

StrictDoc shall avoid using JavaScript-based programming languages.

#### REQUIREMENT: Monolithic application with no microservices @SDOC-SRS-87

> STATUS: Active

> RATIONALE: The project is too small to scale to a multi-service architecture.

> NOTES: This requirement could be re-considered only if a significant technical pressure
would require the use of microservices.

StrictDoc shall avoid using microservices and microservice-based architectures.

#### REQUIREMENT: No reliance on containerization @SDOC-SRS-88

> STATUS: Active

> RATIONALE: Containers are significant extra layer of complexity. They are hard to debug.

> NOTES: This constraint does not block a StrictDoc user from wrapping StrictDoc into their containers.

StrictDoc shall avoid using containers and containerization technologies.

### SECTION-SRS-Coding-constraints @SECTION-SRS-Coding-constraints

> ReqIF.ChapterName: Coding constraints

#### REQUIREMENT: Use of asserts @SDOC-SRS-40

> STATUS: Active

StrictDoc\'s development shall ensure a use of assertions throughout the project codebase. NOTE: At a minimum, the function input parameters must be checked for validity.

#### REQUIREMENT: Use of type annotations in Python code @SDOC-SRS-41

> STATUS: Active

StrictDoc\'s development shall ensure a use of type annotations throughout the project\'s Python codebase.

### SECTION-SRS-Linting @SECTION-SRS-Linting

> ReqIF.ChapterName: Linting

#### REQUIREMENT: Compliance with Python community practices (PEP8 etc) @SDOC-SRS-42

> STATUS: Active

StrictDoc\'s development shall ensure that the project\'s codebase is compliant with the Python community\'s modern practices.

### SECTION-SRS-Static-analysis @SECTION-SRS-Static-analysis

> ReqIF.ChapterName: Static analysis

#### REQUIREMENT: Static type checking @SDOC-SRS-43

> STATUS: Active

StrictDoc\'s development shall include a continuous type checking of StrictDoc\'s codebase.

### SECTION-SRS-Testing @SECTION-SRS-Testing

> ReqIF.ChapterName: Testing

#### REQUIREMENT: Unit testing @SDOC-SRS-44

> STATUS: Active

StrictDoc\'s development shall provide unit testing of its codebase.

#### REQUIREMENT: CLI interface black-box integration testing @SDOC-SRS-45

> STATUS: Active

StrictDoc\'s development shall provide complete black-box integration testing of its command-line interface.

#### REQUIREMENT: Web end-to-end testing @SDOC-SRS-46

> STATUS: Active

StrictDoc\'s development shall provide complete end-to-end testing of the web interface.

#### REQUIREMENT: At least one integration or end-to-end test @SDOC-SRS-47

> STATUS: Active

> RATIONALE: This requirement ensures that every new feature or a chance in the codebase is covered/stressed by at least one test, according to the change type.

Every update to the StrictDoc codebase shall be complemented with a corresponding provision of at least one test as follows: - For web interface: at least one end-to-end test. - For command-line interface: at least one black-box integration test. - For internal Python functions: at least one unit test. NOTE: This requirement implies that no modifications to StrictDoc\'s functionality can be merged unless accompanied by at least one test.
