#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <cctype>
#include <cstdlib>
#include <iomanip>

namespace MiniJson
{
    struct Value
    {
        enum class Type { Null, Bool, Number, String, Array, Object };

        Type type = Type::Null;
        std::string str;                 // String value, or raw text of a Number
        std::vector<Value> arr;          // Array items, or Object values
        std::vector<std::string> keys;   // Object keys (parallel to arr)

        bool isArray()  const { return type == Type::Array; }
        bool isObject() const { return type == Type::Object; }
        bool isString() const { return type == Type::String; }
        bool isNumber() const { return type == Type::Number; }

        const Value* find(const std::string& key) const
        {
            if (type != Type::Object) return nullptr;
            for (size_t i = 0; i < keys.size(); ++i)
                if (keys[i] == key) return &arr[i];
            return nullptr;
        }
    };

    class Parser
    {
    public:
        explicit Parser(const std::string& text) : s(text), p(0)
        {
            // skip UTF-8 BOM
            if (s.size() >= 3 && (unsigned char)s[0] == 0xEF &&
                (unsigned char)s[1] == 0xBB && (unsigned char)s[2] == 0xBF)
                p = 3;
        }

        Value parse()
        {
            Value v = parseValue();
            skipWs();
            if (p != s.size()) fail("unexpected trailing characters");
            return v;
        }

    private:
        const std::string& s;
        size_t p;

        [[noreturn]] void fail(const std::string& msg) const
        {
            throw std::runtime_error("JSON parse error at offset " + std::to_string(p) + ": " + msg);
        }

        void skipWs()
        {
            while (p < s.size() && std::isspace((unsigned char)s[p])) ++p;
        }

        char peek()
        {
            skipWs();
            if (p >= s.size()) fail("unexpected end of input");
            return s[p];
        }

        void expect(char c)
        {
            if (peek() != c) fail(std::string("expected '") + c + "'");
            ++p;
        }

        bool match(const char* lit)
        {
            size_t n = std::char_traits<char>::length(lit);
            if (s.compare(p, n, lit) == 0) { p += n; return true; }
            return false;
        }

        Value parseValue()
        {
            char c = peek();
            if (c == '{') return parseObject();
            if (c == '[') return parseArray();
            if (c == '"') { Value v; v.type = Value::Type::String; v.str = parseString(); return v; }
            if (c == '-' || std::isdigit((unsigned char)c)) return parseNumber();
            if (match("true"))  { Value v; v.type = Value::Type::Bool; v.str = "true";  return v; }
            if (match("false")) { Value v; v.type = Value::Type::Bool; v.str = "false"; return v; }
            if (match("null"))  { return Value(); }
            fail("unexpected character");
        }

        Value parseObject()
        {
            Value v; v.type = Value::Type::Object;
            expect('{');
            if (peek() == '}') { ++p; return v; }
            for (;;) {
                if (peek() != '"') fail("expected string key");
                std::string key = parseString();
                expect(':');
                v.keys.push_back(std::move(key));
                v.arr.push_back(parseValue());
                char c = peek();
                if (c == ',') { ++p; continue; }
                if (c == '}') { ++p; break; }
                fail("expected ',' or '}'");
            }
            return v;
        }

        Value parseArray()
        {
            Value v; v.type = Value::Type::Array;
            expect('[');
            if (peek() == ']') { ++p; return v; }
            for (;;) {
                v.arr.push_back(parseValue());
                char c = peek();
                if (c == ',') { ++p; continue; }
                if (c == ']') { ++p; break; }
                fail("expected ',' or ']'");
            }
            return v;
        }

        Value parseNumber()
        {
            size_t start = p;
            if (s[p] == '-') ++p;
            while (p < s.size() && (std::isdigit((unsigned char)s[p]) || s[p] == '.' ||
                   s[p] == 'e' || s[p] == 'E' || s[p] == '+' || s[p] == '-'))
                ++p;
            Value v; v.type = Value::Type::Number;
            v.str = s.substr(start, p - start);
            return v;
        }

        static void appendUtf8(std::string& out, unsigned cp)
        {
            if (cp < 0x80) out += (char)cp;
            else if (cp < 0x800) {
                out += (char)(0xC0 | (cp >> 6));
                out += (char)(0x80 | (cp & 0x3F));
            } else {
                out += (char)(0xE0 | (cp >> 12));
                out += (char)(0x80 | ((cp >> 6) & 0x3F));
                out += (char)(0x80 | (cp & 0x3F));
            }
        }

        std::string parseString()
        {
            expect('"');
            std::string out;
            while (p < s.size()) {
                char c = s[p++];
                if (c == '"') return out;
                if (c != '\\') { out += c; continue; }

                if (p >= s.size()) break;
                char e = s[p++];
                switch (e) {
                    case '"':  out += '"';  break;
                    case '\\': out += '\\'; break;
                    case '/':  out += '/';  break;
                    case 'b':  out += '\b'; break;
                    case 'f':  out += '\f'; break;
                    case 'n':  out += '\n'; break;
                    case 'r':  out += '\r'; break;
                    case 't':  out += '\t'; break;
                    case 'u': {
                        if (p + 4 > s.size()) fail("bad \\u escape");
                        unsigned cp = (unsigned)std::strtoul(s.substr(p, 4).c_str(), nullptr, 16);
                        p += 4;
                        appendUtf8(out, cp);
                        break;
                    }
                    default: fail("invalid escape sequence");
                }
            }
            fail("unterminated string");
        }
    };

    static std::string jsonEscape(const std::string& s) {
        std::string o;
        for (char c : s) {
            if (c == '"' || c == '\\') { o += '\\'; o += c; }
            else if (c == '\n') o += "\\n";
            else o += c;
        }
        return o;
    }
    
}