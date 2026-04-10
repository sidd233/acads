Here’s your assignment cleanly written in **Markdown format**:

---

# CD Lab Assignment 11



## Grammar for BibTeX Recognition

Consider the following grammar intended for recognition of a BibTeX file:

```
P → A NL P | B NL P | I NL P | A | B | I

A → @ARTICLE BLOCK1  
B → @BOOK BLOCK2  
I → @INPROCEEDING BLOCK3
```

### BLOCK1

```
BLOCK1 → {article-$TEXT, NL
          TAB author = {TEXT}, NL
          TAB title = {ALPHANUMERIC}, NL
          TAB journal = {TEXT Journal}, NL
          TAB year = DIGIT, NL
          TAB pages = DIGIT, NL
          } NL
```

### BLOCK2

```
BLOCK2 → {book-$TEXT, NL
          TAB author = {TEXT}, NL
          TAB title = {ALPHANUMERIC}, NL
          TAB volume = DIGIT, NL
          TAB publisher = {TEXT}, NL
          } NL
```

### BLOCK3

```
BLOCK3 → {inproceedings-$TEXT, NL
          TAB author = {TEXT}, NL
          TAB title = {ALPHANUMERIC}, NL
          TAB editor = {TEXT}, NL
          TAB series = {TEXT}, NL
          TAB year = DIGIT, NL
          TAB publisher = {ALPHANUMERIC}, NL
          } NL
```

### TEXT Rule

```
$TEXT → full | minimal | crossref | journal
```

---

## Notes

* Keywords include:
  `@ARTICLE, @BOOK, @INPROCEEDING, article, title, journal, year, pages, volume, publisher, editor, series, full, minimal, crossref, journal, NL, TAB, {, }, = , ,`

* `NL` represents newline

* `TEXT` represents a word (sequence of alphabets only)

* `ALPHANUMERIC` represents a string including spaces with alphabets and digits

* `DIGIT` represents a sequence of digits

---

## Questions

### 1.

Write the **lex and yacc programs** for this grammar.

* Your parser should:

  * Detect syntax errors
  * Print appropriate error messages
  * Indicate:

    * Position of error
    * Nature of error (lexical or grammatical)
  * You may terminate on detecting the first error

---

### 2.

Use this program to:

* Convert the corresponding BibTeX file into an XML file
* Ensure appropriate tags are generated as specified

---

## Sample BibTeX Input

```
@ARTICLE{article-full,
author={Leslie},
title={The Gnats and Gnus Document Preparation System},
journal={Animal},
year=1986,
page=73,
}

@BOOK{book-full,
author={Donald},
title={Seminumerical Algorithms},
volume=2,
publisher={Addison Wesley},
}

@INPROCEEDINGS{inproceedings-minimal,
author={Alfred},
title={Lower Bounds on wishful research results},
editor={Wizard},
series={ACM},
year=1990,
publisher={Academic Press},
}

@BOOK{book-full,
author={Donald},
title={Seminumerical Algorithms},
volume=2,
publisher={Addison Wesley},
}
```

---

## Sample XML Output

```
<document>

<ARTICLE>
<article>full</article>
<author>Leslie</author>
<title>The Gnats and Gnus Document Preparation System</title>
<journal>Animal</journal>
<year>1986</year>
<page>73</page>
</ARTICLE>

<BOOK>
<book>full</book>
<author>Donald</author>
<title>Seminumerical Algorithms</title>
<volume>2</volume>
<publisher>Addison Wesley</publisher>
</BOOK>

<INPROCEEDINGS>
<inproceedings>minimal</inproceedings>
<author>Alfred</author>
<title>Lower Bounds on wishful research results</title>
<editor>Wizard</editor>
<series>ACM</series>
<year>1990</year>
<publisher>Academic Press</publisher>
</INPROCEEDINGS>

<BOOK>
<book>full</book>
<author>Donald</author>
<title>Seminumerical Algorithms</title>
<volume>2</volume>
<publisher>Addison Wesley</publisher>
</BOOK>

</document>
```

---

If you want, next step we can:

* write the **actual lex + yacc code**, or
* convert this into a **perfect README submission format**.

