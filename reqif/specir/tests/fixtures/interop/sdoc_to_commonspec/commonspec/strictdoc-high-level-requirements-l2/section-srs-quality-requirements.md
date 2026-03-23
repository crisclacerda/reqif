## SECTION-SRS-Quality-requirements @SECTION-SRS-Quality-requirements

> ReqIF.ChapterName: Development process requirements

### SECTION-12b09bf0-84cb-4adb-8960-004f814c337e @SECTION-022

> ReqIF.ChapterName: General process

#### REQUIREMENT: Priority handling of critical issues in StrictDoc @SDOC-SRS-133

> STATUS: Active

> RATIONALE: Prioritizing major issues ensures StrictDoc remains stable and reliable, preventing serious problems that could compromise its performance and integrity.

### SECTION-SRS-Requirements-engineering @SECTION-SRS-Requirements-engineering

> ReqIF.ChapterName: Requirements engineering

#### REQUIREMENT: Requirements-based development @SDOC-SRS-128

> STATUS: Active

#### REQUIREMENT: Self-hosted requirements @SDOC-SRS-91

> STATUS: Active

### SECTION-SRS-Implementation-requirements @SECTION-SRS-Implementation-requirements

> ReqIF.ChapterName: Implementation requirements

#### SECTION-SRS-Programming-languages @SECTION-SRS-Programming-languages

> ReqIF.ChapterName: Programming languages

##### REQUIREMENT: Python language @SDOC-SRS-8

> STATUS: Active

> RATIONALE: Python has an excellent package ecosystem. It is a widely used language. It is most often the next language for C/C++ programming community when it comes to the tools development and scripting tasks.

#### SECTION-SRS-Cross-platform-availability @SECTION-SRS-Cross-platform-availability

> ReqIF.ChapterName: Cross-platform availability

##### REQUIREMENT: Linux @SDOC-SRS-9

> STATUS: Active

##### REQUIREMENT: macOS @SDOC-SRS-10

> STATUS: Active

##### REQUIREMENT: Windows @SDOC-SRS-11

> STATUS: Active

### SECTION-SRS-Implementation-constraints @SECTION-SRS-Implementation-constraints

> ReqIF.ChapterName: Implementation constraints

#### REQUIREMENT: Use of open source components @SDOC-SRS-89

> STATUS: Active

> RATIONALE: No commercial/proprietary dependency chain ensures that StrictDoc remain free and open for everyone.

#### REQUIREMENT: No heavy UI frameworks @SDOC-SRS-14

> STATUS: Active

#### REQUIREMENT: No use of NPM @SDOC-SRS-15

> STATUS: Active

> RATIONALE: StrictDoc already deals with the Python/Pip/Pypi ecosystem. The amount of necessary maintenance is already quite high. NPM is known for splitting its projects into very small parts, which increases the complexity of maintaining all dependencies.

#### REQUIREMENT: No use of JavaScript replacement languages (e.g., Typescript) @SDOC-SRS-16

> STATUS: Active

> RATIONALE: The development team does not have specific experience with any of the JS alternatives. Staying with a general subset of JavaScript is a safer choice.

#### REQUIREMENT: Monolithic application with no microservices @SDOC-SRS-87

> STATUS: Active

> RATIONALE: The project is too small to scale to a multi-service architecture.

> NOTES: This requirement could be re-considered only if a significant technical pressure
would require the use of microservices.

#### REQUIREMENT: No reliance on containerization @SDOC-SRS-88

> STATUS: Active

> RATIONALE: Containers are significant extra layer of complexity. They are hard to debug.

> NOTES: This constraint does not block a StrictDoc user from wrapping StrictDoc into their containers.

### SECTION-SRS-Coding-constraints @SECTION-SRS-Coding-constraints

> ReqIF.ChapterName: Coding constraints

#### REQUIREMENT: Use of asserts @SDOC-SRS-40

> STATUS: Active

#### REQUIREMENT: Use of type annotations in Python code @SDOC-SRS-41

> STATUS: Active

### SECTION-SRS-Linting @SECTION-SRS-Linting

> ReqIF.ChapterName: Linting

#### REQUIREMENT: Compliance with Python community practices (PEP8 etc) @SDOC-SRS-42

> STATUS: Active

### SECTION-SRS-Static-analysis @SECTION-SRS-Static-analysis

> ReqIF.ChapterName: Static analysis

#### REQUIREMENT: Static type checking @SDOC-SRS-43

> STATUS: Active

### SECTION-SRS-Testing @SECTION-SRS-Testing

> ReqIF.ChapterName: Testing

#### REQUIREMENT: Unit testing @SDOC-SRS-44

> STATUS: Active

#### REQUIREMENT: CLI interface black-box integration testing @SDOC-SRS-45

> STATUS: Active

#### REQUIREMENT: Web end-to-end testing @SDOC-SRS-46

> STATUS: Active

#### REQUIREMENT: At least one integration or end-to-end test @SDOC-SRS-47

> STATUS: Active

> RATIONALE: This requirement ensures that every new feature or a chance in the codebase is covered/stressed by at least one test, according to the change type.
