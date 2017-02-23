# Change Log

(as of v0.2.0)

## 0.2.1

* Fix handling of special characters in deposit receipts - unicode strings with non-ascii characters were breaking the xml parsing
* Fix behaviour when location header is added to deposit receipt, so "location" and "edit" are always the same