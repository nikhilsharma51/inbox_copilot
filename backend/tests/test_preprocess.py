import pytest
import time
from ai_pipeline.preprocess import clean_email
from ai_pipeline.config import MAX_BODY_CHARS


class TestCleanEmail:
    def test_hostile_html_hidden_elements(self):
        html = """
        <div>Visible text</div>
        <div style="display:none">Hidden text</div>
        <span style="visibility: hidden">Also hidden</span>
        <span style="font-size:0">Zero size</span>
        <script>alert('xss')</script>
        <!-- comment -->
        """
        result = clean_email(html)
        assert 'Visible text' in result
        assert 'Hidden text' not in result
        assert 'Also hidden' not in result
        assert 'Zero size' not in result
        assert 'alert' not in result
        assert 'comment' not in result

    def test_large_body_performance(self):
        large_text = "word " * 200000
        start = time.time()
        result = clean_email(large_text)
        elapsed = time.time() - start
        
        assert elapsed < 2.0
        assert len(result) <= MAX_BODY_CHARS + len(' [truncated]')

    def test_emoji_and_non_latin_survive(self):
        text = "Hello 👋 مرحبا 你好 🎉"
        result = clean_email(text)
        assert '👋' in result
        assert 'مرحبا' in result
        assert '你好' in result
        assert '🎉' in result

    def test_zero_width_characters_removed(self):
        text = "ig\u200bnore"
        result = clean_email(text)
        assert result == "ignore"

    def test_otp_code_redacted_before_truncation(self):
        otp_code = "123456"
        text = ("x" * (MAX_BODY_CHARS - 50)) + f" verification code: {otp_code}"
        result = clean_email(text)
        
        assert otp_code not in result
        assert "[REDACTED_CODE]" in result

    def test_card_number_redacted(self):
        card = "4111 1111 1111 1111"
        text = f"Your card: {card}"
        result = clean_email(text)
        
        assert card not in result
        assert "[REDACTED_NUMBER]" in result

    def test_url_query_string_stripped(self):
        text = "Visit https://example.com/page?id=123&token=abc"
        result = clean_email(text)
        
        assert "https://example.com/page" in result
        assert "?id=123" not in result
        assert "token=abc" not in result

    def test_quoted_reply_cut(self):
        text = """
        My response here.
        
        On Mon, Nov 10, 2024 at 10:00 AM User wrote:
        > Original message
        > Line 2
        """
        result = clean_email(text)
        
        assert "My response here" in result
        assert "Original message" not in result

    def test_quoted_lines_cut(self):
        text = """
        Response
        > Quoted line 1
        > Quoted line 2
        """
        result = clean_email(text)
        
        assert "Response" in result
        assert "> Quoted line 1" not in result

    def test_signature_cut(self):
        text = """
        Thank you,
        John
        --
        This is a signature
        """
        result = clean_email(text)
        
        assert "Thank you" in result
        assert "This is a signature" not in result

    def test_sent_from_footer_cut(self):
        text = """
        Message here
        
        Sent from my iPhone
        """
        result = clean_email(text)
        
        assert "Message here" in result
        assert "Sent from my iPhone" not in result

    def test_confidentiality_notice_cut(self):
        text = """
        Important message
        
        Confidentiality notice: This email is confidential
        """
        result = clean_email(text)
        
        assert "Important message" in result
        assert "Confidentiality notice" not in result

    def test_plain_text_unchanged_except_normalization(self):
        text = "Plain text email with\nno special formatting"
        result = clean_email(text)
        
        assert "Plain text email" in result
        assert "no special formatting" in result

    def test_truncation_with_suffix(self):
        long_text = "word " * 500
        result = clean_email(long_text)
        
        assert len(result) <= MAX_BODY_CHARS + len(' [truncated]')
        assert result.endswith(' [truncated]')

    def test_4_digit_code_redacted(self):
        text = "Your code is 1234"
        result = clean_email(text)
        
        assert "1234" not in result
        assert "[REDACTED_CODE]" in result

    def test_8_digit_code_redacted(self):
        text = "verification: 12345678"
        result = clean_email(text)
        
        assert "12345678" not in result
        assert "[REDACTED_CODE]" in result

    def test_13_digit_number_redacted(self):
        text = "Number: 1234567890123"
        result = clean_email(text)
        
        assert "[REDACTED_NUMBER]" in result

    def test_19_digit_number_redacted(self):
        text = "Number: 1234567890123456789"
        result = clean_email(text)
        
        assert "[REDACTED_NUMBER]" in result

    def test_number_with_dashes_redacted(self):
        text = "Card: 1234-5678-9012-3456"
        result = clean_email(text)
        
        assert "[REDACTED_NUMBER]" in result

    def test_otp_near_code_keyword(self):
        text = "OTP code is 123456 please verify"
        result = clean_email(text)
        
        assert "123456" not in result
        assert "[REDACTED_CODE]" in result

    def test_empty_input(self):
        result = clean_email("")
        assert result == ""

    def test_html_comments_removed(self):
        html = "<div>Text</div><!-- This is a comment -->"
        result = clean_email(html)
        
        assert "Text" in result
        assert "comment" not in result

    def test_script_tags_removed(self):
        html = "<div>Content</div><script>malicious code</script>"
        result = clean_email(html)
        
        assert "Content" in result
        assert "malicious" not in result

    def test_style_tags_removed(self):
        html = "<div>Text</div><style>.hidden { display: none; }</style>"
        result = clean_email(html)
        
        assert "Text" in result
        assert "hidden" not in result or "display" not in result

    def test_code_keyword_context_40_chars(self):
        text = "a" * 38 + " code 1234"
        result = clean_email(text)
        assert "[REDACTED_CODE]" in result

    def test_verification_keyword_context(self):
        text = "Please verification 123456"
        result = clean_email(text)
        assert "[REDACTED_CODE]" in result
