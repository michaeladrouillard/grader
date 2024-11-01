from typing import List, Dict

class MarkdownReport:
    def generate(self, results: List[Dict]) -> str:
        """
        Generate a formatted Markdown report from assessment results.
        """
        markdown = "# Repository Assessment Report\n\n"
        
        total_score = 0
        total_items = len(results)
        
        for result in results:
            item = result['item']
            assessment = result['assessment']
            
            markdown += f"## {item['title']}\n\n"
            markdown += f"**Score:** {assessment['score']}/100\n\n"
            markdown += f"**Reasoning:** {assessment['reason']}\n\n"
            
            if 'confidence' in assessment:
                markdown += f"**Confidence:** {assessment['confidence']:.2f}\n\n"
            
            markdown += "---\n\n"
            
            total_score += assessment['score']
        
        # add summary section
        average_score = total_score / total_items
        markdown += f"# Summary\n\n"
        markdown += f"**Overall Score:** {average_score:.2f}/100\n\n"
        
        return markdown